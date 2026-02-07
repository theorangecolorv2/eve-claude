#!/usr/bin/env python3
"""Диагностический тест Linux memory reader для EVE Online.

Запуск:
    python scripts/test_linux_reader.py

Тест проходит 7 этапов, каждый проверяет один слой:
    1. Поиск процесса EVE
    2. Доступ к /proc/pid/mem
    3. Чтение /proc/pid/maps
    4. Поиск PyTypeObject (метаклассы)
    5. Поиск типа UIRoot
    6. Поиск экземпляров UIRoot
    7. Полное чтение UI tree + сохранение JSON

Каждый этап подробно логирует что происходит.
Если этап падает — видно где именно проблема.
"""

import json
import logging
import os
import struct
import sys
import time
from pathlib import Path

# Добавить корень проекта в path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Настройка подробного логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('test_linux_reader')

# Отключить слишком шумные логгеры
logging.getLogger('urllib3').setLevel(logging.WARNING)


def check_platform():
    """Этап 0: проверка платформы."""
    logger.info("=" * 60)
    logger.info("ЭТАП 0: Проверка платформы")
    logger.info("=" * 60)

    logger.info(f"sys.platform = {sys.platform}")
    logger.info(f"os.name = {os.name}")
    logger.info(f"Python = {sys.version}")

    if sys.platform != 'linux':
        logger.error("Этот скрипт только для Linux!")
        logger.info("На Windows используйте scripts/test_sanderling.py")
        return False

    # Проверить ptrace_scope
    try:
        with open('/proc/sys/kernel/yama/ptrace_scope', 'r') as f:
            ptrace_scope = f.read().strip()
        logger.info(f"ptrace_scope = {ptrace_scope}")
        if ptrace_scope != '0':
            logger.warning(
                f"ptrace_scope = {ptrace_scope} (не 0). "
                "Чтение памяти другого процесса может не работать.\n"
                "Исправить: echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope"
            )
    except FileNotFoundError:
        logger.info("ptrace_scope не найден (возможно, не используется YAMA)")

    return True


def stage1_find_process():
    """Этап 1: найти процесс EVE Online."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("ЭТАП 1: Поиск процесса EVE Online")
    logger.info("=" * 60)

    from core.sanderling.linux_process import find_eve_process

    pid = find_eve_process()
    if not pid:
        logger.error("Процесс EVE Online не найден!")
        logger.info("")
        logger.info("Подсказки:")
        logger.info("  - EVE запущена через Steam Proton?")
        logger.info("  - Проверьте: ps aux | grep -i exe")
        logger.info("  - Ищем 'exefile.exe' в /proc/*/cmdline")
        logger.info("")

        # Показать все Wine-процессы для отладки
        logger.info("Все Wine/Proton процессы:")
        for entry in os.listdir('/proc'):
            if not entry.isdigit():
                continue
            try:
                with open(f'/proc/{entry}/cmdline', 'rb') as f:
                    cmdline = f.read().decode('utf-8', errors='replace')
                if 'wine' in cmdline.lower() or 'proton' in cmdline.lower() or '.exe' in cmdline.lower():
                    cmdline_display = cmdline.replace('\x00', ' ')[:200]
                    logger.info(f"  PID {entry}: {cmdline_display}")
            except (OSError, PermissionError):
                continue

        return None

    logger.info(f"✓ Найден PID: {pid}")

    # Показать детали процесса
    try:
        with open(f'/proc/{pid}/cmdline', 'rb') as f:
            cmdline = f.read().decode('utf-8', errors='replace').replace('\x00', ' ')
        logger.info(f"  cmdline: {cmdline[:300]}")

        with open(f'/proc/{pid}/status', 'r') as f:
            for line in f:
                if line.startswith(('Name:', 'Pid:', 'PPid:', 'Uid:', 'VmSize:', 'VmRSS:')):
                    logger.info(f"  {line.strip()}")
    except OSError:
        pass

    return pid


def stage2_access_memory(pid):
    """Этап 2: проверить доступ к /proc/pid/mem."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("ЭТАП 2: Доступ к памяти процесса")
    logger.info("=" * 60)

    from core.sanderling.linux_process import LinuxProcessAccess

    process = LinuxProcessAccess(pid)
    if not process.open():
        logger.error("Не удалось открыть /proc/pid/mem!")
        logger.info("")
        logger.info("Подсказки:")
        logger.info("  - Запустите от того же пользователя что и EVE")
        logger.info("  - Или: echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope")
        logger.info("  - Или запустите с sudo (не рекомендуется)")
        return None

    method = "process_vm_readv" if process._use_process_vm_readv else "/proc/pid/mem (pread)"
    logger.info(f"✓ Доступ к памяти открыт ({method})")

    # Тест: прочитать несколько байт из начала процесса
    # Пробуем прочитать из первого readable региона
    from core.sanderling.linux_process import get_memory_regions
    regions = get_memory_regions(pid)
    readable = [r for r in regions if r.is_readable and r.size >= 64]

    if readable:
        test_region = readable[0]
        data = process.read_bytes(test_region.start, 16)
        if data:
            hex_data = ' '.join(f'{b:02X}' for b in data)
            logger.info(f"✓ Тестовое чтение 16 байт @ 0x{test_region.start:X}: {hex_data}")
        else:
            logger.warning(f"✗ Не удалось прочитать из 0x{test_region.start:X}")
    else:
        logger.warning("Нет readable регионов!")

    return process


def stage3_memory_map(pid):
    """Этап 3: анализ /proc/pid/maps."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("ЭТАП 3: Карта памяти процесса")
    logger.info("=" * 60)

    from core.sanderling.linux_process import get_memory_regions

    regions = get_memory_regions(pid)
    logger.info(f"Всего регионов: {len(regions)}")

    readable = [r for r in regions if r.is_readable]
    writable = [r for r in regions if r.is_writable]
    heap = [r for r in regions if '[heap]' in r.pathname]
    anon = [r for r in regions if not r.pathname or r.pathname.startswith('[')]

    total_readable = sum(r.size for r in readable)
    total_anon = sum(r.size for r in anon if r.is_readable)

    logger.info(f"Readable: {len(readable)} ({total_readable / 1024 / 1024:.0f} MB)")
    logger.info(f"Writable: {len(writable)}")
    logger.info(f"Heap: {len(heap)} ({sum(r.size for r in heap) / 1024 / 1024:.0f} MB)")
    logger.info(f"Anonymous readable: {len([r for r in anon if r.is_readable])} ({total_anon / 1024 / 1024:.0f} MB)")

    # Показать крупнейшие регионы
    readable.sort(key=lambda r: r.size, reverse=True)
    logger.info("")
    logger.info("Топ-10 крупнейших readable регионов:")
    for r in readable[:10]:
        logger.info(f"  0x{r.start:012X}-0x{r.end:012X} ({r.size/1024/1024:.1f} MB) {r.permissions} {r.pathname}")

    return regions


def stage4_find_type_objects(pid, process):
    """Этап 4: поиск PyTypeObject (метаклассов)."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("ЭТАП 4: Поиск Python type-объектов (метаклассы)")
    logger.info("=" * 60)

    from core.sanderling.linux_cpython import CPythonReader, OB_TYPE, TP_NAME
    from core.sanderling.linux_process import get_memory_regions

    cpython = CPythonReader(process)
    regions = get_memory_regions(pid)
    readable = [r for r in regions if r.is_readable and r.size >= 4096]

    # Сканируем только первые несколько крупных регионов для теста
    type_objects = []
    scan_limit = 50 * 1024 * 1024  # 50 MB для быстрого теста
    scanned = 0

    logger.info(f"Сканируем до {scan_limit / 1024 / 1024:.0f} MB readable памяти...")
    start_time = time.time()

    for region in readable:
        if scanned >= scan_limit:
            break

        chunk_size = min(4 * 1024 * 1024, region.size)
        data = process.read_bytes(region.start, chunk_size)
        if data is None:
            continue

        scanned += chunk_size

        for i in range(0, len(data) - 32, 8):
            potential_type = struct.unpack_from('<Q', data, i + OB_TYPE)[0]
            if potential_type < 0x1000 or potential_type > 0x7FFFFFFFFFFF:
                continue

            addr = region.start + i
            if cpython.is_type_metaclass(addr):
                name_ptr = process.read_uint64(addr + TP_NAME)
                if name_ptr:
                    name = process.read_cstring(name_ptr, 64)
                    if name and name.isprintable() and len(name) < 64:
                        type_objects.append((addr, name))

    elapsed = time.time() - start_time
    logger.info(f"Сканировано {scanned / 1024 / 1024:.0f} MB за {elapsed:.1f}s")
    logger.info(f"Найдено type-объектов: {len(type_objects)}")

    if type_objects:
        # Показать найденные типы
        logger.info("")
        logger.info("Найденные Python типы (первые 50):")
        # Группируем по имени
        type_names = {}
        for addr, name in type_objects:
            if name not in type_names:
                type_names[name] = []
            type_names[name].append(addr)

        for name in sorted(type_names.keys())[:50]:
            addrs = type_names[name]
            addr_str = ', '.join(f'0x{a:X}' for a in addrs[:3])
            if len(addrs) > 3:
                addr_str += f' ... (+{len(addrs)-3})'
            logger.info(f"  {name}: {addr_str}")

        # Проверить есть ли EVE-специфичные типы
        eve_types = [n for n in type_names if n in (
            'UIRoot', 'Container', 'Window', 'Label', 'Sprite',
            'LayerCore', 'Fill', 'Transform', 'EveLabelSmall',
            'OverviewScrollEntry', 'TargetInBar', 'ShipSlot',
            'PyChildrenList', 'ContextMenu'
        )]
        if eve_types:
            logger.info("")
            logger.info(f"✓ Найдены EVE UI типы: {', '.join(eve_types)}")
        else:
            logger.warning("✗ EVE UI типы не найдены в просканированном диапазоне")
            logger.info("  Попробуйте увеличить scan_limit или проверить что EVE загружена")
    else:
        logger.error("✗ Python type-объекты не найдены!")
        logger.info("  Возможные причины:")
        logger.info("  - EVE ещё не полностью загружена")
        logger.info("  - Неправильный PID")
        logger.info("  - Структура памяти отличается от ожидаемой")

    return type_objects, cpython


def stage5_find_uiroot(pid, process, cpython):
    """Этап 5: поиск типа UIRoot."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("ЭТАП 5: Поиск UIRoot")
    logger.info("=" * 60)

    from core.sanderling.linux_reader import LinuxMemoryReader

    reader = LinuxMemoryReader(pid)
    reader._process = process
    reader._cpython = cpython

    from core.sanderling.linux_process import get_memory_regions
    regions = get_memory_regions(pid)
    readable = [r for r in regions if r.is_readable and r.size > 0]

    logger.info("Поиск ВСЕХ PyTypeObject с именем 'UIRoot'...")
    start_time = time.time()

    uiroot_types = reader._find_all_uiroot_types(readable)

    elapsed = time.time() - start_time

    if uiroot_types:
        logger.info(f"✓ Найдено {len(uiroot_types)} типов UIRoot (за {elapsed:.1f}s)")

        for i, type_addr in enumerate(uiroot_types):
            logger.info(f"")
            logger.info(f"  --- UIRoot тип #{i+1}: 0x{type_addr:X} ---")

            tp_name_ptr = process.read_uint64(type_addr + 0x18)
            if tp_name_ptr:
                name = process.read_cstring(tp_name_ptr, 64)
                logger.info(f"  tp_name = '{name}'")

            tp_basicsize = process.read_int64(type_addr + 0x20)
            logger.info(f"  tp_basicsize = {tp_basicsize}")

            # tp_dictoffset
            from core.sanderling.linux_reader import TP_DICTOFFSET_CANDIDATES
            dict_offset = None
            for offset in TP_DICTOFFSET_CANDIDATES:
                val = process.read_int64(type_addr + offset)
                if val is not None and 0x10 <= val <= 0x200:
                    dict_offset = val
                    logger.info(f"  tp_dictoffset (@ 0x{offset:X}) = {val} (0x{val:X})")
                    break

            if dict_offset is None:
                logger.warning("  tp_dictoffset не найден")
    else:
        logger.error(f"✗ Типы UIRoot не найдены (искали {elapsed:.1f}s)")
        logger.info("  Подсказки:")
        logger.info("  - EVE полностью загружена? (дождитесь экрана выбора персонажа)")
        logger.info("  - Попробуйте запустить повторно")
        return [], reader

    return uiroot_types, reader


def stage6_find_instances(pid, process, cpython, uiroot_types, reader):
    """Этап 6: поиск валидных экземпляров UIRoot."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("ЭТАП 6: Поиск экземпляров UIRoot")
    logger.info("=" * 60)

    from core.sanderling.linux_process import get_memory_regions
    regions = get_memory_regions(pid)
    readable = [r for r in regions if r.is_readable and r.size > 0]

    best_addr = None
    best_count = 0

    for type_addr in uiroot_types:
        dict_offset = reader._get_dict_offset_for_type(type_addr)
        logger.info(f"Тип 0x{type_addr:X}: tp_dictoffset = {dict_offset}")

        logger.info(f"  Поиск объектов с ob_type = 0x{type_addr:X}...")
        start_time = time.time()

        instances = reader._find_instances_of_type(readable, type_addr)
        elapsed = time.time() - start_time
        logger.info(f"  Найдено {len(instances)} кандидатов (за {elapsed:.1f}s)")

        # Валидация
        valid = 0
        invalid_reasons = {"bad_refcnt": 0, "no_dict": 0}

        for addr in instances:
            # Проверка refcnt
            refcnt = process.read_int64(addr)
            if refcnt is None or refcnt <= 0 or refcnt > 10_000_000:
                invalid_reasons["bad_refcnt"] += 1
                continue

            # Проверка __dict__
            has_dict = False
            if dict_offset and dict_offset > 0:
                dict_ptr = process.read_uint64(addr + dict_offset)
                if dict_ptr:
                    dict_type = cpython.read_type_name(dict_ptr)
                    if dict_type == 'dict':
                        has_dict = True

            if not has_dict:
                # Brute-force dict поиск
                for off in (0x10, 0x18, 0x20, 0x28, 0x30, 0x38, 0x40, 0x48):
                    ptr = process.read_uint64(addr + off)
                    if ptr and cpython.read_type_name(ptr) == 'dict':
                        has_dict = True
                        logger.debug(f"    0x{addr:X}: dict найден brute-force @ 0x{off:X}")
                        break

            if not has_dict:
                invalid_reasons["no_dict"] += 1
                continue

            valid += 1

            # Посчитать ноды
            reader._visited.clear()
            count = reader._count_tree_nodes(addr, depth=0)
            logger.info(f"  ✓ 0x{addr:X}: refcnt={refcnt}, {count} нод")

            if count > best_count:
                best_count = count
                best_addr = addr

        logger.info(f"  Валидных: {valid}, отброшено: "
                     f"bad_refcnt={invalid_reasons['bad_refcnt']}, "
                     f"no_dict={invalid_reasons['no_dict']}")

    if best_addr and best_count > 1:
        logger.info(f"")
        logger.info(f"✓ Лучший UIRoot: 0x{best_addr:X} ({best_count} нод)")

        # Показать содержимое __dict__
        dict_addr = reader._find_instance_dict(best_addr)
        if dict_addr:
            raw_dict = cpython.read_dict(dict_addr)
            if raw_dict:
                logger.info(f"  Ключи __dict__ ({len(raw_dict)}):")
                for key in sorted(raw_dict.keys()):
                    logger.info(f"    '{key}'")
    else:
        logger.error(f"✗ Валидные экземпляры UIRoot не найдены!")
        logger.info("")
        logger.info("  Детальная диагностика первых 5 кандидатов:")

        # Показать что на самом деле лежит по offsets у первого кандидата
        for type_addr in uiroot_types:
            instances = reader._find_instances_of_type(readable, type_addr)
            for addr in instances[:5]:
                logger.info(f"")
                logger.info(f"  Кандидат 0x{addr:X} (type 0x{type_addr:X}):")
                refcnt = process.read_int64(addr)
                logger.info(f"    ob_refcnt = {refcnt}")
                for off in range(0x00, 0x58, 0x08):
                    ptr = process.read_uint64(addr + off)
                    if ptr:
                        tname = cpython.read_type_name(ptr) if 0x1000 < ptr < 0x7FFFFFFFFFFF else None
                        hex_ptr = f"0x{ptr:X}"
                        type_info = f" (type: {tname})" if tname else ""
                        logger.info(f"    offset 0x{off:02X} → {hex_ptr}{type_info}")

        return None

    return best_addr


def stage7_read_tree(pid, process, cpython, root_addr):
    """Этап 7: полное чтение UI tree."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("ЭТАП 7: Чтение UI tree")
    logger.info("=" * 60)

    from core.sanderling.linux_reader import LinuxMemoryReader

    reader = LinuxMemoryReader(pid)
    reader._process = process
    reader._cpython = cpython

    root_str = f"0x{root_addr:X}"
    logger.info(f"Чтение UI tree от {root_str}...")
    start_time = time.time()

    tree = reader.read_ui_tree(root_str)

    elapsed_ms = (time.time() - start_time) * 1000
    node_count = len(reader._visited)

    if not tree:
        logger.error("✗ Не удалось прочитать UI tree!")
        return None

    logger.info(f"✓ UI tree прочитан: {node_count} нод за {elapsed_ms:.0f}ms")

    # Анализ дерева
    logger.info("")
    logger.info("Анализ UI tree:")
    logger.info(f"  root type: {tree.get('pythonObjectTypeName')}")
    logger.info(f"  root address: {tree.get('pythonObjectAddress')}")

    dict_entries = tree.get('dictEntriesOfInterest', {})
    logger.info(f"  dictEntriesOfInterest keys: {list(dict_entries.keys())}")

    if '_name' in dict_entries:
        logger.info(f"  _name: {dict_entries['_name']}")
    if '_displayWidth' in dict_entries:
        w = dict_entries['_displayWidth']
        if isinstance(w, dict):
            w = w.get('int_low32', w)
        logger.info(f"  _displayWidth: {w}")
    if '_displayHeight' in dict_entries:
        h = dict_entries['_displayHeight']
        if isinstance(h, dict):
            h = h.get('int_low32', h)
        logger.info(f"  _displayHeight: {h}")

    children = tree.get('children', [])
    if children:
        logger.info(f"  Дочерних узлов: {len(children)}")
        for i, child in enumerate(children[:10]):
            c_type = child.get('pythonObjectTypeName', '?')
            c_dict = child.get('dictEntriesOfInterest', {})
            c_name = c_dict.get('_name', '')
            c_children = child.get('children')
            c_count = len(c_children) if c_children else 0
            logger.info(f"    [{i}] {c_type} name='{c_name}' children={c_count}")
    else:
        logger.warning("  Нет дочерних узлов!")

    # Рекурсивная статистика типов
    type_counts = {}
    _count_types(tree, type_counts)
    logger.info(f"")
    logger.info(f"Статистика типов ({len(type_counts)} уникальных):")
    for name, count in sorted(type_counts.items(), key=lambda x: -x[1])[:30]:
        logger.info(f"  {name}: {count}")

    # Сохранить JSON
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"linux_ui_tree_{timestamp}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(tree, f, indent=2, ensure_ascii=False)

    logger.info(f"")
    logger.info(f"✓ JSON сохранён: {output_file}")
    logger.info(f"  Размер: {output_file.stat().st_size / 1024:.0f} KB")

    # Попробовать парсинг через parser.py
    logger.info("")
    logger.info("Тест парсинга через UITreeParser...")
    try:
        from core.sanderling.parser import UITreeParser
        parser = UITreeParser()
        state = parser.parse(tree)

        logger.info(f"  is_valid: {state.is_valid}")
        logger.info(f"  warnings: {state.warnings}")
        logger.info(f"  targets: {len(state.targets)}")
        logger.info(f"  overview: {len(state.overview)}")
        if state.ship:
            logger.info(f"  ship.shield: {state.ship.shield:.1%}")
            logger.info(f"  ship.armor: {state.ship.armor:.1%}")
            logger.info(f"  ship.hull: {state.ship.hull:.1%}")
            logger.info(f"  modules: {len(state.ship.modules)}")
        logger.info(f"✓ Парсинг успешен!")
    except Exception as e:
        logger.error(f"✗ Ошибка парсинга: {e}")
        import traceback
        traceback.print_exc()

    return tree


def _count_types(node, counts):
    """Рекурсивно подсчитать типы узлов."""
    if not isinstance(node, dict):
        return
    type_name = node.get('pythonObjectTypeName', '?')
    counts[type_name] = counts.get(type_name, 0) + 1
    children = node.get('children', [])
    if isinstance(children, list):
        for child in children:
            _count_types(child, counts)


def main():
    logger.info("╔══════════════════════════════════════════════════════════╗")
    logger.info("║  Диагностика Linux Memory Reader для EVE Online         ║")
    logger.info("╚══════════════════════════════════════════════════════════╝")
    logger.info("")

    # Этап 0
    if not check_platform():
        sys.exit(1)

    # Этап 1
    pid = stage1_find_process()
    if not pid:
        sys.exit(1)

    # Этап 2
    process = stage2_access_memory(pid)
    if not process:
        sys.exit(1)

    # Этап 3
    regions = stage3_memory_map(pid)

    # Этап 4
    type_objects, cpython = stage4_find_type_objects(pid, process)

    # Этап 5
    uiroot_types, reader = stage5_find_uiroot(pid, process, cpython)
    if not uiroot_types:
        process.close()
        sys.exit(1)

    # Этап 6
    root_addr = stage6_find_instances(pid, process, cpython, uiroot_types, reader)
    if not root_addr:
        process.close()
        sys.exit(1)

    # Этап 7
    tree = stage7_read_tree(pid, process, cpython, root_addr)

    # Итог
    process.close()
    logger.info("")
    logger.info("=" * 60)
    if tree:
        logger.info("РЕЗУЛЬТАТ: УСПЕХ ✓")
        logger.info("Linux memory reader работает!")
    else:
        logger.info("РЕЗУЛЬТАТ: ЧАСТИЧНЫЙ УСПЕХ")
        logger.info("UIRoot найден, но чтение дерева имеет проблемы.")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
