"""Оркестратор чтения UI tree EVE Online на Linux.

Заменяет read-memory-64-bit.exe для Linux.
Читает память напрямую через /proc/pid/mem,
парсит CPython 2.7 объекты и строит UI tree
в том же JSON-формате что и C# exe.
"""

import logging
import struct
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from .linux_process import LinuxProcessAccess, MemoryRegion, get_memory_regions
from .linux_cpython import CPythonReader, OB_TYPE, OB_SIZE, TP_NAME

logger = logging.getLogger(__name__)

# ============================================================
# Offset tp_dictoffset внутри PyTypeObject (Windows x64 CPython 2.7)
#
# EVE Online использует Stackless Python 2.7 скомпилированный MSVC для Win64.
# На Windows x64 long=4 байта, что сдвигает offsets после tp_flags.
# Полная раскладка PyTypeObject (Win64 CPython 2.7):
#
#   0x00  ob_refcnt      (Py_ssize_t = 8)
#   0x08  ob_type        (ptr = 8)
#   0x10  ob_size        (Py_ssize_t = 8)
#   0x18  tp_name        (ptr = 8)
#   0x20  tp_basicsize   (Py_ssize_t = 8)
#   0x28  tp_itemsize    (Py_ssize_t = 8)
#   0x30  tp_dealloc     (ptr = 8)
#   0x38  tp_print       (ptr = 8)
#   0x40  tp_getattr     (ptr = 8)
#   0x48  tp_setattr     (ptr = 8)
#   0x50  tp_compare     (ptr = 8)
#   0x58  tp_repr        (ptr = 8)
#   0x60  tp_as_number   (ptr = 8)
#   0x68  tp_as_sequence (ptr = 8)
#   0x70  tp_as_mapping  (ptr = 8)
#   0x78  tp_hash        (ptr = 8)
#   0x80  tp_call        (ptr = 8)
#   0x88  tp_str         (ptr = 8)
#   0x90  tp_getattro    (ptr = 8)
#   0x98  tp_setattro    (ptr = 8)
#   0xA0  tp_as_buffer   (ptr = 8)
#   0xA8  tp_flags       (long = 4 на Win64!) + 4 padding
#   0xB0  tp_doc         (ptr = 8)
#   0xB8  tp_traverse    (ptr = 8)
#   0xC0  tp_clear       (ptr = 8)
#   0xC8  tp_richcompare (ptr = 8)
#   0xD0  tp_weaklistoffset (Py_ssize_t = 8)
#   0xD8  tp_iter        (ptr = 8)
#   0xE0  tp_iternext    (ptr = 8)
#   0xE8  tp_methods     (ptr = 8)
#   0xF0  tp_members     (ptr = 8)
#   0xF8  tp_getset      (ptr = 8)
#   0x100 tp_base        (ptr = 8)
#   0x108 tp_dict        (ptr = 8)
#   0x110 tp_descr_get   (ptr = 8)
#   0x118 tp_descr_set   (ptr = 8)
#   0x120 tp_dictoffset  (Py_ssize_t = 8) ← ЭТО НАМ НУЖНО
#   0x128 tp_init        (ptr = 8)
#   0x130 tp_alloc       (ptr = 8)
#   0x138 tp_new         (ptr = 8)
#   ...
#
# ВАЖНО: Эти offsets могут отличаться для Stackless Python!
# Stackless добавляет поля в PyTypeObject.
# Поэтому мы пробуем несколько вариантов + brute-force.
# ============================================================

# Возможные offsets tp_dictoffset для разных сборок CPython 2.7
# (стандартный CPython, Stackless Python, с/без отладочных полей)
TP_DICTOFFSET_CANDIDATES = [0x120, 0x128, 0x130, 0x118, 0x110]

# Ключи dict которые считаются "entries of interest" (аналог C# логики)
ENTRIES_OF_INTEREST_KEYS = {
    '_top', '_left', '_width', '_height',
    '_displayX', '_displayY', '_displayWidth', '_displayHeight',
    '_display', '_opacity', '_name',
    '_setText', '_text', '_hint',
    '_texturePath', 'texturePath',
    '_color', '_bgColor',
    'ramp_active', 'checked',
    '_lastValue',
    '_sr',
    'children',
}

# Максимальная глубина обхода UI tree
MAX_TREE_DEPTH = 40
# Максимальное количество детей у одного узла
MAX_CHILDREN = 500
# Максимальный размер чанка для сканирования (4 MB)
DEFAULT_SCAN_CHUNK_SIZE = 4 * 1024 * 1024


class LinuxMemoryReader:
    """Чтение UI tree EVE Online из памяти Linux-процесса."""

    def __init__(self, pid: int, scan_chunk_size: int = DEFAULT_SCAN_CHUNK_SIZE):
        self.pid = pid
        self.scan_chunk_size = scan_chunk_size
        self._process: Optional[LinuxProcessAccess] = None
        self._cpython: Optional[CPythonReader] = None
        self._visited: Set[int] = set()
        # Кэш: type_addr → dict_offset (или None если нет __dict__)
        self._dictoffset_cache: Dict[int, Optional[int]] = {}
        # Калиброванный offset tp_dictoffset внутри PyTypeObject
        self._tp_dictoffset_offset: Optional[int] = None

    def open(self) -> bool:
        """
        Открыть доступ к памяти процесса.

        Returns:
            True если успешно
        """
        self._process = LinuxProcessAccess(self.pid)
        if not self._process.open():
            return False
        self._cpython = CPythonReader(self._process)
        return True

    def close(self) -> None:
        """Закрыть доступ к памяти."""
        if self._process:
            self._process.close()
            self._process = None
        self._cpython = None

    def find_root_address(self) -> Optional[str]:
        """
        Найти адрес UIRoot в памяти процесса.

        Алгоритм:
        1. Получить readable регионы из /proc/pid/maps
        2. Найти ВСЕ типы с именем "UIRoot" (может быть несколько после reload)
        3. Для каждого типа найти экземпляры
        4. Валидировать экземпляры (ob_refcnt + __dict__ проверка)
        5. Вернуть адрес с максимальным количеством нод

        Returns:
            Адрес в формате "0xABCD..." или None
        """
        if not self._process or not self._cpython:
            logger.error("Процесс не открыт")
            return None

        logger.info("Поиск UIRoot в памяти процесса...")
        start_time = time.time()

        # Шаг 1: получить readable регионы
        regions = get_memory_regions(self.pid)
        readable_regions = [r for r in regions if r.is_readable and r.size > 0]
        total_size = sum(r.size for r in readable_regions)
        logger.info(f"Найдено {len(readable_regions)} readable регионов, "
                     f"всего {total_size / 1024 / 1024:.0f} MB")

        # Шаг 2: найти ВСЕ типы с именем "UIRoot"
        uiroot_types = self._find_all_uiroot_types(readable_regions)
        if not uiroot_types:
            logger.error("Тип UIRoot не найден в памяти")
            return None

        logger.info(f"Найдено {len(uiroot_types)} типов UIRoot: "
                     f"{', '.join(f'0x{a:X}' for a in uiroot_types)}")

        # Шаг 3-4: для каждого типа найти и валидировать экземпляры
        best_addr = None
        best_count = 0

        for type_addr in uiroot_types:
            # Прочитать tp_dictoffset для этого типа
            dict_offset = self._get_dict_offset_for_type(type_addr)
            logger.info(f"Тип 0x{type_addr:X}: tp_dictoffset = {dict_offset}")

            instances = self._find_instances_of_type(readable_regions, type_addr)
            logger.info(f"  Найдено {len(instances)} кандидатов")

            # Валидация и подсчёт нод
            valid_count = 0
            for addr in instances:
                if not self._validate_instance(addr, dict_offset):
                    continue

                valid_count += 1
                self._visited.clear()
                count = self._count_tree_nodes(addr, depth=0)
                logger.debug(f"  ✓ 0x{addr:X}: {count} нод (валидный)")

                if count > best_count:
                    best_count = count
                    best_addr = addr

            logger.info(f"  Из них валидных: {valid_count}")

        if best_addr is None or best_count <= 1:
            logger.error(f"Не удалось найти валидный UIRoot (лучший: {best_count} нод)")
            return None

        elapsed = time.time() - start_time
        root_hex = f"0x{best_addr:X}"
        logger.info(f"Найден UIRoot: {root_hex} ({best_count} нод) за {elapsed:.1f}s")

        return root_hex

    def _validate_instance(self, addr: int, dict_offset: Optional[int]) -> bool:
        """
        Проверить что адрес действительно является экземпляром Python-объекта.

        Фильтрует false positives — ссылки на тип внутри MRO, tp_subclasses и т.д.

        Args:
            addr: Адрес кандидата
            dict_offset: Ожидаемый offset __dict__ (из tp_dictoffset)

        Returns:
            True если это валидный экземпляр
        """
        # Проверка 1: ob_refcnt должен быть разумным (>0, <10M)
        refcnt = self._process.read_int64(addr)
        if refcnt is None or refcnt <= 0 or refcnt > 10_000_000:
            return False

        # Проверка 2: если знаем dict_offset, проверить что там dict
        if dict_offset and dict_offset > 0:
            dict_ptr = self._process.read_uint64(addr + dict_offset)
            if dict_ptr is None or dict_ptr == 0:
                return False
            dict_type = self._cpython.read_type_name(dict_ptr)
            if dict_type != 'dict':
                return False

        return True

    def _get_dict_offset_for_type(self, type_addr: int) -> Optional[int]:
        """
        Прочитать tp_dictoffset из PyTypeObject.

        Args:
            type_addr: Адрес PyTypeObject

        Returns:
            Значение tp_dictoffset или None
        """
        for candidate in TP_DICTOFFSET_CANDIDATES:
            val = self._process.read_int64(type_addr + candidate)
            if val is not None and 0x10 <= val <= 0x200:
                return val
        return None

    def read_ui_tree(self, root_address: str) -> Optional[dict]:
        """
        Прочитать UI tree начиная с root address.

        Формат выхода совместим с C# exe:
        {
            "pythonObjectAddress": "2174746181248",
            "pythonObjectTypeName": "UIRoot",
            "dictEntriesOfInterest": {...},
            "otherDictEntriesKeys": null,
            "children": [...]
        }

        Args:
            root_address: Адрес в формате "0xABCD..." или decimal string

        Returns:
            UI tree dict или None
        """
        if not self._process or not self._cpython:
            logger.error("Процесс не открыт")
            return None

        # Парсить адрес
        addr = self._parse_address(root_address)
        if addr is None:
            logger.error(f"Невалидный адрес: {root_address}")
            return None

        self._visited.clear()
        start_time = time.time()

        tree = self._read_node(addr, depth=0)

        elapsed_ms = (time.time() - start_time) * 1000
        node_count = len(self._visited)
        logger.info(f"UI tree прочитан: {node_count} нод за {elapsed_ms:.0f}ms")

        return tree

    def _find_all_uiroot_types(self, regions: List[MemoryRegion]) -> List[int]:
        """
        Найти ВСЕ PyTypeObject с именем "UIRoot".

        Быстрый алгоритм (вместо перебора каждого 8-byte aligned адреса):
        1. Найти все вхождения C-строки "UIRoot\\0" в памяти (bytes.find — O(n))
        2. Для каждого адреса строки — искать указатель на неё (tp_name)
        3. Верифицировать что найденный объект — PyTypeObject (метакласс)

        Args:
            regions: Список readable регионов

        Returns:
            Список адресов PyTypeObject
        """
        # Шаг 1: найти все вхождения строки "UIRoot\0" в памяти
        target = b"UIRoot\x00"
        string_addrs = []

        # Сканируем только anonymous/heap регионы (пропускаем .so файлы)
        scan_regions = [r for r in regions if self._is_heap_region(r)]
        total_scan = sum(r.size for r in scan_regions)
        logger.info(f"Шаг 1: поиск строки 'UIRoot' в {len(scan_regions)} регионах "
                     f"({total_scan / 1024 / 1024:.0f} MB)")

        for region in scan_regions:
            offset = 0
            while offset < region.size:
                chunk_size = min(self.scan_chunk_size, region.size - offset)
                chunk_addr = region.start + offset

                data = self._process.read_bytes(chunk_addr, chunk_size)
                if data is None:
                    offset += chunk_size
                    continue

                # bytes.find — C-оптимизирован, очень быстро
                search_start = 0
                while True:
                    pos = data.find(target, search_start)
                    if pos == -1:
                        break
                    string_addrs.append(chunk_addr + pos)
                    search_start = pos + 1

                offset += chunk_size

        logger.info(f"  Найдено {len(string_addrs)} вхождений строки 'UIRoot'")

        if not string_addrs:
            return []

        # Шаг 2: для каждого адреса строки — искать PyTypeObject с tp_name → этот адрес
        # tp_name (0x18) содержит указатель на C-строку
        result = []

        for str_addr in string_addrs:
            # Упаковать адрес строки для поиска в памяти
            str_addr_bytes = struct.pack('<Q', str_addr)

            for region in scan_regions:
                offset = 0
                while offset < region.size:
                    chunk_size = min(self.scan_chunk_size, region.size - offset)
                    chunk_addr = region.start + offset

                    data = self._process.read_bytes(chunk_addr, chunk_size)
                    if data is None:
                        offset += chunk_size
                        continue

                    search_start = 0
                    while True:
                        pos = data.find(str_addr_bytes, search_start)
                        if pos == -1:
                            break

                        # Этот указатель должен быть на позиции tp_name (0x18)
                        # Значит PyTypeObject начинается на 0x18 раньше
                        if pos >= TP_NAME:
                            type_addr = chunk_addr + pos - TP_NAME

                            # Верификация: это реально type-объект?
                            if (type_addr % 8 == 0 and
                                    type_addr not in [r for r, _ in result] and
                                    self._cpython.is_type_metaclass(type_addr)):
                                # Дополнительная проверка: tp_name действительно указывает на строку
                                verify_ptr = self._process.read_uint64(type_addr + TP_NAME)
                                if verify_ptr == str_addr:
                                    logger.debug(f"Найден тип UIRoot @ 0x{type_addr:X} "
                                                 f"(tp_name → 0x{str_addr:X})")
                                    result.append(type_addr)

                        search_start = pos + 1

                    offset += chunk_size

            # Если уже нашли хотя бы один тип — можно не искать по остальным строкам
            # (но продолжаем для надёжности)

        # Дедупликация
        result = list(set(result))
        logger.info(f"Шаг 2: найдено {len(result)} типов UIRoot")
        return result

    @staticmethod
    def _is_heap_region(region: MemoryRegion) -> bool:
        """
        Проверить что регион содержит heap/anonymous данные (не библиотечный код).

        Python объекты живут только в heap и anonymous mmap регионах.
        Пропускаем .so/.dll файлы, vdso, vvar и т.д.
        """
        # Должен быть readable
        if not region.is_readable:
            return False

        # Пропускаем файловые маппинги (.so, .dll, и т.д.)
        path = region.pathname.strip()
        if path and not path.startswith('['):
            # Файловый маппинг — пропускаем
            return False

        # Пропускаем специальные регионы ядра
        if path in ('[vdso]', '[vvar]', '[vsyscall]'):
            return False

        # Слишком маленькие регионы
        if region.size < 4096:
            return False

        return True

    def _find_instances_of_type(self, regions: List[MemoryRegion], type_addr: int) -> List[int]:
        """
        Найти все экземпляры с указанным ob_type.

        Сканирует только heap/anonymous регионы (Python объекты не в .so файлах).

        Args:
            regions: Список readable регионов
            type_addr: Адрес PyTypeObject

        Returns:
            Список адресов экземпляров
        """
        instances = []
        type_bytes = struct.pack('<Q', type_addr)
        scan_regions = [r for r in regions if self._is_heap_region(r)]

        for region in scan_regions:
            offset = 0
            while offset < region.size:
                chunk_size = min(self.scan_chunk_size, region.size - offset)
                chunk_addr = region.start + offset

                data = self._process.read_bytes(chunk_addr, chunk_size)
                if data is None:
                    offset += chunk_size
                    continue

                # bytes.find для поиска type_addr — быстро
                search_start = 0
                while True:
                    pos = data.find(type_bytes, search_start)
                    if pos == -1:
                        break

                    # ob_type находится по offset 0x08
                    if pos >= OB_TYPE and (pos - OB_TYPE) % 8 == 0:
                        obj_addr = chunk_addr + pos - OB_TYPE
                        instances.append(obj_addr)

                    search_start = pos + 1

                offset += chunk_size

        return instances

    def _count_tree_nodes(self, addr: int, depth: int) -> int:
        """
        Посчитать количество нод в поддереве (для выбора лучшего кандидата).

        Args:
            addr: Адрес узла
            depth: Текущая глубина

        Returns:
            Количество нод
        """
        if depth > MAX_TREE_DEPTH or addr in self._visited:
            return 0

        self._visited.add(addr)

        # Проверить что это валидный Python-объект
        type_name = self._cpython.read_type_name(addr)
        if type_name is None:
            return 0

        count = 1

        # Попробовать найти children
        children_addrs = self._get_children_addresses(addr)
        if children_addrs:
            for child_addr in children_addrs:
                count += self._count_tree_nodes(child_addr, depth + 1)

        return count

    def _read_node(self, addr: int, depth: int) -> Optional[dict]:
        """
        Рекурсивно прочитать узел UI tree.

        Args:
            addr: Адрес PyObject
            depth: Текущая глубина

        Returns:
            dict в формате C# exe или None
        """
        if depth > MAX_TREE_DEPTH or addr in self._visited:
            return None

        self._visited.add(addr)

        # Прочитать тип
        type_name = self._cpython.read_type_name(addr)
        if type_name is None:
            return None

        # Прочитать __dict__
        dict_entries_of_interest = {}
        other_keys = None

        dict_addr = self._find_instance_dict(addr)
        if dict_addr:
            raw_dict = self._cpython.read_dict(dict_addr)
            if raw_dict:
                interest_keys = []
                other_key_list = []

                for key, value_addr in raw_dict.items():
                    if key in ENTRIES_OF_INTEREST_KEYS:
                        interest_keys.append((key, value_addr))
                    else:
                        other_key_list.append(key)

                # Читаем значения entries of interest
                for key, value_addr in interest_keys:
                    value = self._read_dict_value(key, value_addr, depth)
                    if value is not None:
                        dict_entries_of_interest[key] = value

                # other keys — null при --remove-other-dict-entries (как C# exe)
                other_keys = None

        # Прочитать children
        children = None
        children_addrs = self._get_children_addresses(addr)
        if children_addrs:
            children = []
            for child_addr in children_addrs[:MAX_CHILDREN]:
                child_node = self._read_node(child_addr, depth + 1)
                if child_node:
                    children.append(child_node)

            if not children:
                children = None

        return {
            "pythonObjectAddress": str(addr),
            "pythonObjectTypeName": type_name,
            "dictEntriesOfInterest": dict_entries_of_interest,
            "otherDictEntriesKeys": other_keys,
            "children": children,
        }

    def _read_dict_value(self, key: str, value_addr: int, depth: int) -> Any:
        """
        Прочитать значение из dict для entries of interest.

        Воспроизводит формат C# exe:
        - int (маленький, < 2^31): просто число
        - int (большой): {"int": "addr_decimal", "int_low32": low32}
        - str/unicode: строка
        - float: число
        - bool: True/False
        - children ref: {"address": "...", "pythonObjectTypeName": "..."}
        - объект с __dict__: {"entriesOfInterest": {...}}

        Args:
            key: Ключ словаря
            value_addr: Адрес значения
            depth: Текущая глубина

        Returns:
            Значение в формате C# exe
        """
        if value_addr == 0:
            return None

        type_name = self._cpython.read_type_name(value_addr)
        if type_name is None:
            return None

        if type_name == 'str':
            return self._cpython.read_string(value_addr)

        elif type_name == 'unicode':
            return self._cpython.read_unicode(value_addr)

        elif type_name == 'int':
            val = self._cpython.read_int(value_addr)
            if val is None:
                return None

            # Маленькие int (помещаются в int32) — просто число
            if -2147483648 <= val <= 2147483647:
                return val

            # Большие int — формат C# exe с int и int_low32
            low32 = val & 0xFFFFFFFF
            # Если low32 > 2^31, конвертировать в signed int32
            if low32 > 0x7FFFFFFF:
                low32 = low32 - 0x100000000
            return {
                "int": str(value_addr),
                "int_low32": low32
            }

        elif type_name == 'float':
            return self._cpython.read_float(value_addr)

        elif type_name == 'bool':
            return self._cpython.read_bool(value_addr)

        elif type_name == 'NoneType':
            return None

        elif type_name == 'PyChildrenList' or key == 'children':
            # Ссылка на children — в C# формате это объект с address и type
            return {
                "address": str(value_addr),
                "pythonObjectTypeName": type_name
            }

        else:
            # Для других объектов, если у них есть __dict__, читаем entriesOfInterest
            sub_dict_addr = self._find_instance_dict(value_addr)
            if sub_dict_addr:
                raw_dict = self._cpython.read_dict(sub_dict_addr)
                if raw_dict:
                    entries = {}
                    for k, v_addr in raw_dict.items():
                        if k in ENTRIES_OF_INTEREST_KEYS:
                            v = self._read_dict_value(k, v_addr, depth + 1)
                            if v is not None:
                                entries[k] = v
                    return {"entriesOfInterest": entries}

            return None

    def _find_instance_dict(self, addr: int) -> Optional[int]:
        """
        Найти __dict__ экземпляра Python-объекта.

        Стратегия (от быстрой к медленной):
        1. Проверить кэш type → dict_offset
        2. Попробовать прочитать tp_dictoffset из PyTypeObject
        3. Brute-force: перебрать типичные offsets и проверить что там dict

        Args:
            addr: Адрес Python-объекта

        Returns:
            Адрес PyDictObject или None
        """
        type_addr = self._process.read_uint64(addr + OB_TYPE)
        if type_addr is None or type_addr == 0:
            return None

        # Шаг 1: кэш
        if type_addr in self._dictoffset_cache:
            cached_offset = self._dictoffset_cache[type_addr]
            if cached_offset is None:
                return None
            potential_dict = self._process.read_uint64(addr + cached_offset)
            if potential_dict and self._cpython.read_type_name(potential_dict) == 'dict':
                return potential_dict

        # Шаг 2: tp_dictoffset из PyTypeObject
        dict_offset = self._read_tp_dictoffset(type_addr)
        if dict_offset and dict_offset > 0:
            potential_dict = self._process.read_uint64(addr + dict_offset)
            if potential_dict and self._cpython.read_type_name(potential_dict) == 'dict':
                self._dictoffset_cache[type_addr] = dict_offset
                return potential_dict

        # Шаг 3: brute-force
        # Для EVE UI объектов __dict__ обычно рядом с началом объекта
        for offset in (0x10, 0x18, 0x20, 0x28, 0x30, 0x38, 0x40, 0x48):
            potential_dict = self._process.read_uint64(addr + offset)
            if potential_dict is None or potential_dict == 0:
                continue

            dict_type_name = self._cpython.read_type_name(potential_dict)
            if dict_type_name == 'dict':
                self._dictoffset_cache[type_addr] = offset
                logger.debug(f"Brute-force dict offset для type 0x{type_addr:X}: 0x{offset:X}")
                return potential_dict

        # Не нашли — кэшируем как None
        self._dictoffset_cache[type_addr] = None
        return None

    def _read_tp_dictoffset(self, type_addr: int) -> Optional[int]:
        """
        Попробовать прочитать tp_dictoffset из PyTypeObject.

        Args:
            type_addr: Адрес PyTypeObject

        Returns:
            tp_dictoffset значение или None
        """
        # Если уже знаем правильный offset — используем его
        if self._tp_dictoffset_offset is not None:
            val = self._process.read_int64(type_addr + self._tp_dictoffset_offset)
            if val is not None and 0x10 <= val <= 0x200:
                return val
            return None

        # Пробуем кандидаты
        for candidate in TP_DICTOFFSET_CANDIDATES:
            val = self._process.read_int64(type_addr + candidate)
            if val is not None and 0x10 <= val <= 0x200:
                # Валидация: проверяем что на этом offset в объекте действительно dict
                # (нужен хотя бы один объект этого типа — но мы не знаем его адрес)
                # Запоминаем кандидат, проверим при первом использовании
                logger.debug(f"tp_dictoffset кандидат: offset=0x{candidate:X} → value=0x{val:X}")
                return val

        return None

    def _get_children_addresses(self, addr: int) -> Optional[List[int]]:
        """
        Получить адреса дочерних узлов.

        Children хранятся в атрибуте 'children' который является
        PyChildrenList (обёртка над Python list).

        Args:
            addr: Адрес узла

        Returns:
            Список адресов детей или None
        """
        # Найти __dict__
        dict_addr = self._find_instance_dict(addr)
        if not dict_addr:
            return None

        # Найти 'children' в dict
        raw_dict = self._cpython.read_dict(dict_addr)
        if not raw_dict or 'children' not in raw_dict:
            return None

        children_obj_addr = raw_dict['children']

        # children может быть PyChildrenList или обычный list
        children_type = self._cpython.read_type_name(children_obj_addr)

        if children_type == 'list':
            return self._cpython.read_list(children_obj_addr, MAX_CHILDREN)

        elif children_type in ('PyChildrenList', 'PyObjectChildrenList'):
            # PyChildrenList содержит Python list внутри
            # Пробуем найти list внутри PyChildrenList
            child_dict_addr = self._find_instance_dict(children_obj_addr)
            if child_dict_addr:
                child_dict = self._cpython.read_dict(child_dict_addr)
                if child_dict:
                    # Ищем атрибут содержащий list (обычно '_items' или '_childrenObjects')
                    for key in ('_childrenObjects', '_items', 'items', '_list'):
                        if key in child_dict:
                            list_addr = child_dict[key]
                            list_type = self._cpython.read_type_name(list_addr)
                            if list_type == 'list':
                                return self._cpython.read_list(list_addr, MAX_CHILDREN)

            # Fallback: PyChildrenList может наследовать от list
            # Пробуем прочитать как list напрямую
            result = self._cpython.read_list(children_obj_addr, MAX_CHILDREN)
            if result:
                return result

        return None

    @staticmethod
    def _parse_address(address: str) -> Optional[int]:
        """
        Распарсить адрес из строки.

        Поддерживает форматы: "0xABCD", "12345" (decimal).

        Args:
            address: Строка с адресом

        Returns:
            int или None
        """
        try:
            address = address.strip()
            if address.startswith('0x') or address.startswith('0X'):
                return int(address, 16)
            else:
                return int(address)
        except (ValueError, TypeError):
            return None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args):
        self.close()
