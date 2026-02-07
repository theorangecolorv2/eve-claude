"""Чтение объектов CPython 2.7 из памяти процесса.

EVE Online использует встроенный CPython 2.7 (64-bit).
Этот модуль читает Python-объекты напрямую из памяти,
используя известные offsets структур CPython.

Offsets для 64-bit CPython 2.7:
- PyObject:     ob_refcnt (0x00), ob_type (0x08)
- PyVarObject:  ob_size (0x10)
- PyTypeObject: tp_name (0x18)
- PyDictObject: ma_fill (0x10), ma_used (0x18), ma_mask (0x20), ma_table (0x28)
- PyStringObject: ob_shash (0x18), ob_sstate (0x20), ob_sval (0x24, inline)
- PyUnicodeObject: length (0x10), str_ptr (0x18)
- PyIntObject:  ob_ival (0x10)
- PyFloatObject: ob_fval (0x10)
- PyListObject: ob_size (0x10), ob_item (0x18)
- PyBoolObject: ob_ival (0x10) — 0 = False, 1 = True
"""

import logging
from typing import Any, Dict, List, Optional, Set, Tuple

from .linux_process import LinuxProcessAccess

logger = logging.getLogger(__name__)

# Offsets для CPython 2.7 (64-bit)
OB_REFCNT = 0x00
OB_TYPE = 0x08
OB_SIZE = 0x10  # PyVarObject.ob_size

# PyTypeObject offsets (от начала объекта)
TP_NAME = 0x18  # char* tp_name (указатель на C-строку)

# PyDictObject offsets
DICT_MA_FILL = 0x10
DICT_MA_USED = 0x18
DICT_MA_MASK = 0x20
DICT_MA_TABLE = 0x28

# PyDictEntry — sizeof = 24 байт (3 указателя)
DICTENTRY_HASH = 0x00
DICTENTRY_KEY = 0x08
DICTENTRY_VALUE = 0x10
DICTENTRY_SIZE = 24

# PyStringObject offsets
STR_OB_SHASH = 0x18
STR_OB_SSTATE = 0x20
STR_OB_SVAL = 0x24  # inline char array

# PyUnicodeObject offsets (CPython 2.7)
UNICODE_LENGTH = 0x10
UNICODE_STR = 0x18  # Py_UNICODE* str

# PyIntObject
INT_OB_IVAL = 0x10

# PyFloatObject
FLOAT_OB_FVAL = 0x10

# PyListObject
LIST_OB_SIZE = 0x10
LIST_OB_ITEM = 0x18  # PyObject** ob_item

# Максимальная глубина рекурсии для чтения объектов
MAX_DEPTH = 10
# Максимальная длина строки
MAX_STRING_LEN = 4096
# Максимальный размер dict
MAX_DICT_SIZE = 10000
# Максимальный размер list
MAX_LIST_SIZE = 10000


class CPythonReader:
    """Чтение CPython 2.7 объектов из памяти процесса."""

    def __init__(self, process: LinuxProcessAccess):
        self.process = process
        # Кэш имён типов для производительности
        self._type_name_cache: Dict[int, str] = {}
        # Кэш metaclass проверок
        self._metaclass_cache: Dict[int, bool] = {}

    def read_type_name(self, obj_addr: int) -> Optional[str]:
        """
        Прочитать имя типа Python-объекта.

        Args:
            obj_addr: Адрес PyObject

        Returns:
            Имя типа или None
        """
        type_addr = self.process.read_uint64(obj_addr + OB_TYPE)
        if type_addr is None or type_addr == 0:
            return None

        # Проверить кэш
        if type_addr in self._type_name_cache:
            return self._type_name_cache[type_addr]

        # tp_name — указатель на C-строку
        name_ptr = self.process.read_uint64(type_addr + TP_NAME)
        if name_ptr is None or name_ptr == 0:
            return None

        name = self.process.read_cstring(name_ptr, 128)
        if name:
            self._type_name_cache[type_addr] = name
        return name

    def read_type_addr(self, obj_addr: int) -> Optional[int]:
        """
        Прочитать адрес типа Python-объекта.

        Args:
            obj_addr: Адрес PyObject

        Returns:
            Адрес типа или None
        """
        return self.process.read_uint64(obj_addr + OB_TYPE)

    def is_type_metaclass(self, type_addr: int) -> bool:
        """
        Проверить является ли тип метаклассом (ob_type->ob_type == ob_type).

        У type-объектов (PyTypeObject) тип указывает сам на себя
        через цепочку: type->ob_type == type (для встроенного 'type').

        Args:
            type_addr: Адрес предполагаемого PyTypeObject

        Returns:
            True если это метакласс
        """
        if type_addr in self._metaclass_cache:
            return self._metaclass_cache[type_addr]

        # Прочитать ob_type текущего объекта
        meta_type = self.process.read_uint64(type_addr + OB_TYPE)
        if meta_type is None or meta_type == 0:
            self._metaclass_cache[type_addr] = False
            return False

        # Прочитать ob_type мета-типа
        meta_meta_type = self.process.read_uint64(meta_type + OB_TYPE)

        # Для встроенного 'type': type->ob_type->ob_type == type->ob_type
        result = meta_type == meta_meta_type
        self._metaclass_cache[type_addr] = result
        return result

    def read_string(self, addr: int) -> Optional[str]:
        """
        Прочитать Python str (bytes в CPython 2.7).

        Args:
            addr: Адрес PyStringObject

        Returns:
            str или None
        """
        # ob_size — длина строки
        size = self.process.read_int64(addr + OB_SIZE)
        if size is None or size < 0 or size > MAX_STRING_LEN:
            return None

        if size == 0:
            return ""

        # ob_sval — inline массив char (начинается с offset 0x24)
        data = self.process.read_bytes(addr + STR_OB_SVAL, size)
        if data is None:
            return None

        try:
            return data.decode('utf-8', errors='replace')
        except Exception:
            return None

    def read_unicode(self, addr: int) -> Optional[str]:
        """
        Прочитать Python unicode (CPython 2.7 — Py_UNICODE = UCS-2 или UCS-4).

        Args:
            addr: Адрес PyUnicodeObject

        Returns:
            str или None
        """
        length = self.process.read_int64(addr + UNICODE_LENGTH)
        if length is None or length < 0 or length > MAX_STRING_LEN:
            return None

        if length == 0:
            return ""

        str_ptr = self.process.read_uint64(addr + UNICODE_STR)
        if str_ptr is None or str_ptr == 0:
            return None

        # CPython 2.7 на Linux x86_64 обычно использует UCS-4 (4 bytes per char)
        byte_len = length * 4
        data = self.process.read_bytes(str_ptr, byte_len)
        if data is None:
            # Попробовать UCS-2 (2 bytes per char)
            byte_len = length * 2
            data = self.process.read_bytes(str_ptr, byte_len)
            if data is None:
                return None
            try:
                return data.decode('utf-16-le', errors='replace')
            except Exception:
                return None

        try:
            return data.decode('utf-32-le', errors='replace')
        except Exception:
            return None

    def read_int(self, addr: int) -> Optional[int]:
        """
        Прочитать Python int.

        Args:
            addr: Адрес PyIntObject

        Returns:
            int или None
        """
        return self.process.read_int64(addr + INT_OB_IVAL)

    def read_float(self, addr: int) -> Optional[float]:
        """
        Прочитать Python float.

        Args:
            addr: Адрес PyFloatObject

        Returns:
            float или None
        """
        return self.process.read_double(addr + FLOAT_OB_FVAL)

    def read_bool(self, addr: int) -> Optional[bool]:
        """
        Прочитать Python bool (подкласс int в CPython 2.7).

        Args:
            addr: Адрес PyBoolObject

        Returns:
            bool или None
        """
        val = self.process.read_int64(addr + INT_OB_IVAL)
        if val is None:
            return None
        return val != 0

    def read_list(self, addr: int, max_items: int = MAX_LIST_SIZE) -> Optional[List[int]]:
        """
        Прочитать Python list и вернуть адреса элементов.

        Args:
            addr: Адрес PyListObject
            max_items: Максимальное количество элементов

        Returns:
            Список адресов элементов или None
        """
        size = self.process.read_int64(addr + LIST_OB_SIZE)
        if size is None or size < 0 or size > max_items:
            return None

        if size == 0:
            return []

        items_ptr = self.process.read_uint64(addr + LIST_OB_ITEM)
        if items_ptr is None or items_ptr == 0:
            return None

        # Читаем массив указателей (8 байт каждый)
        data = self.process.read_bytes(items_ptr, size * 8)
        if data is None:
            return None

        import struct
        addresses = []
        for i in range(size):
            item_addr = struct.unpack_from('<Q', data, i * 8)[0]
            if item_addr != 0:
                addresses.append(item_addr)

        return addresses

    def read_dict(self, addr: int) -> Optional[Dict[str, int]]:
        """
        Прочитать Python dict (CPython 2.7 hash table).

        Возвращает маппинг строковых ключей на адреса значений.
        Пропускает ключи не являющиеся строками.

        Args:
            addr: Адрес PyDictObject

        Returns:
            Dict[str, int] — ключ → адрес значения, или None
        """
        ma_used = self.process.read_int64(addr + DICT_MA_USED)
        if ma_used is None or ma_used < 0 or ma_used > MAX_DICT_SIZE:
            return None

        ma_mask = self.process.read_int64(addr + DICT_MA_MASK)
        if ma_mask is None or ma_mask < 0:
            return None

        ma_table = self.process.read_uint64(addr + DICT_MA_TABLE)
        if ma_table is None or ma_table == 0:
            return None

        # Количество слотов = ma_mask + 1
        num_slots = ma_mask + 1
        if num_slots > MAX_DICT_SIZE:
            return None

        # Читаем всю таблицу за один вызов
        table_size = num_slots * DICTENTRY_SIZE
        table_data = self.process.read_bytes(ma_table, table_size)
        if table_data is None:
            return None

        import struct
        result = {}
        found = 0

        for i in range(num_slots):
            if found >= ma_used:
                break

            offset = i * DICTENTRY_SIZE
            key_addr = struct.unpack_from('<Q', table_data, offset + DICTENTRY_KEY)[0]
            value_addr = struct.unpack_from('<Q', table_data, offset + DICTENTRY_VALUE)[0]

            # Пустой слот или deleted
            if key_addr == 0 or value_addr == 0:
                continue

            found += 1

            # Читаем ключ (только строки)
            key_type = self.read_type_name(key_addr)
            if key_type == 'str':
                key_str = self.read_string(key_addr)
                if key_str is not None:
                    result[key_str] = value_addr

        return result

    def read_python_value(self, addr: int, depth: int = 0) -> Any:
        """
        Прочитать Python-значение с автоматическим dispatch по типу.

        Args:
            addr: Адрес PyObject
            depth: Текущая глубина рекурсии

        Returns:
            Python-значение или None
        """
        if depth > MAX_DEPTH or addr == 0:
            return None

        type_name = self.read_type_name(addr)
        if type_name is None:
            return None

        if type_name == 'str':
            return self.read_string(addr)
        elif type_name == 'unicode':
            return self.read_unicode(addr)
        elif type_name == 'int':
            return self.read_int(addr)
        elif type_name == 'float':
            return self.read_float(addr)
        elif type_name == 'bool':
            return self.read_bool(addr)
        elif type_name == 'NoneType':
            return None
        elif type_name == 'True':
            return True
        elif type_name == 'False':
            return False

        # Для сложных типов возвращаем метаданные (адрес + тип)
        return {"_addr": addr, "_type": type_name}

    def read_dict_values(self, dict_addr: int, depth: int = 0) -> Optional[Dict[str, Any]]:
        """
        Прочитать Python dict с разрешением значений.

        В отличие от read_dict(), эта функция также читает значения,
        а не только адреса.

        Args:
            dict_addr: Адрес PyDictObject
            depth: Текущая глубина рекурсии

        Returns:
            Dict или None
        """
        if depth > MAX_DEPTH:
            return None

        raw_dict = self.read_dict(dict_addr)
        if raw_dict is None:
            return None

        result = {}
        for key, value_addr in raw_dict.items():
            value = self.read_python_value(value_addr, depth + 1)
            result[key] = value

        return result
