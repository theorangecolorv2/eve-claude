"""Низкоуровневый доступ к памяти Linux-процесса.

Используется для чтения памяти EVE Online через /proc/pid/mem.
EVE запущена через Steam Proton (wine64-preloader + exefile.exe).
"""

import os
import struct
import ctypes
import ctypes.util
import logging
import re
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class MemoryRegion:
    """Регион памяти из /proc/pid/maps."""
    start: int
    end: int
    permissions: str
    offset: int
    device: str
    inode: int
    pathname: str

    @property
    def size(self) -> int:
        return self.end - self.start

    @property
    def is_readable(self) -> bool:
        return 'r' in self.permissions

    @property
    def is_writable(self) -> bool:
        return 'w' in self.permissions


class LinuxProcessAccess:
    """Доступ к памяти Linux-процесса через /proc/pid/mem."""

    def __init__(self, pid: int):
        self.pid = pid
        self._fd: Optional[int] = None
        self._use_process_vm_readv = False
        self._libc = None

    def open(self) -> bool:
        """
        Открыть доступ к памяти процесса.

        Returns:
            True если успешно
        """
        try:
            mem_path = f"/proc/{self.pid}/mem"
            self._fd = os.open(mem_path, os.O_RDONLY)
            logger.info(f"Открыт доступ к памяти процесса {self.pid}")
            return True
        except PermissionError:
            logger.warning(f"Нет доступа к /proc/{self.pid}/mem, пробуем process_vm_readv")
            return self._init_process_vm_readv()
        except OSError as e:
            logger.error(f"Ошибка открытия /proc/{self.pid}/mem: {e}")
            return False

    def _init_process_vm_readv(self) -> bool:
        """
        Инициализировать fallback через process_vm_readv().

        Returns:
            True если успешно
        """
        try:
            libc_name = ctypes.util.find_library("c")
            if not libc_name:
                logger.error("Не найдена libc")
                return False

            self._libc = ctypes.CDLL(libc_name, use_errno=True)
            self._use_process_vm_readv = True
            logger.info(f"Используем process_vm_readv для процесса {self.pid}")
            return True
        except OSError as e:
            logger.error(f"Ошибка загрузки libc: {e}")
            return False

    def close(self) -> None:
        """Закрыть доступ к памяти."""
        if self._fd is not None:
            try:
                os.close(self._fd)
            except OSError:
                pass
            self._fd = None
        self._libc = None

    def read_bytes(self, addr: int, size: int) -> Optional[bytes]:
        """
        Прочитать байты из памяти процесса.

        Args:
            addr: Адрес в памяти
            size: Количество байт

        Returns:
            bytes или None при ошибке
        """
        if size <= 0:
            return b''

        # Защита от невалидных адресов (user-space x86_64: 0 .. 0x7FFFFFFFFFFF)
        if addr < 0 or addr > 0x7FFFFFFFFFFF or addr + size > 0x7FFFFFFFFFFF:
            return None

        if self._use_process_vm_readv:
            return self._read_via_process_vm_readv(addr, size)

        if self._fd is None:
            return None

        try:
            data = os.pread(self._fd, size, addr)
            if len(data) != size:
                return None
            return data
        except (OSError, OverflowError, ValueError):
            return None

    def _read_via_process_vm_readv(self, addr: int, size: int) -> Optional[bytes]:
        """
        Чтение через process_vm_readv() syscall.

        Args:
            addr: Адрес в памяти
            size: Количество байт

        Returns:
            bytes или None при ошибке
        """
        if not self._libc:
            return None

        # struct iovec { void *iov_base; size_t iov_len; }
        class iovec(ctypes.Structure):
            _fields_ = [
                ("iov_base", ctypes.c_void_p),
                ("iov_len", ctypes.c_size_t),
            ]

        buf = ctypes.create_string_buffer(size)
        local_iov = iovec(ctypes.cast(buf, ctypes.c_void_p), size)
        remote_iov = iovec(ctypes.c_void_p(addr), size)

        # ssize_t process_vm_readv(pid_t pid,
        #   const struct iovec *local_iov, unsigned long liovcnt,
        #   const struct iovec *remote_iov, unsigned long riovcnt,
        #   unsigned long flags);
        result = self._libc.process_vm_readv(
            ctypes.c_int(self.pid),
            ctypes.byref(local_iov), ctypes.c_ulong(1),
            ctypes.byref(remote_iov), ctypes.c_ulong(1),
            ctypes.c_ulong(0)
        )

        if result == -1:
            return None

        return buf.raw[:result]

    def read_uint64(self, addr: int) -> Optional[int]:
        """Прочитать unsigned 64-bit int."""
        data = self.read_bytes(addr, 8)
        if data is None:
            return None
        return struct.unpack('<Q', data)[0]

    def read_int64(self, addr: int) -> Optional[int]:
        """Прочитать signed 64-bit int."""
        data = self.read_bytes(addr, 8)
        if data is None:
            return None
        return struct.unpack('<q', data)[0]

    def read_int32(self, addr: int) -> Optional[int]:
        """Прочитать signed 32-bit int."""
        data = self.read_bytes(addr, 4)
        if data is None:
            return None
        return struct.unpack('<i', data)[0]

    def read_uint32(self, addr: int) -> Optional[int]:
        """Прочитать unsigned 32-bit int."""
        data = self.read_bytes(addr, 4)
        if data is None:
            return None
        return struct.unpack('<I', data)[0]

    def read_double(self, addr: int) -> Optional[float]:
        """Прочитать double (64-bit float)."""
        data = self.read_bytes(addr, 8)
        if data is None:
            return None
        return struct.unpack('<d', data)[0]

    def read_cstring(self, addr: int, max_len: int = 256) -> Optional[str]:
        """
        Прочитать C-строку (null-terminated).

        Args:
            addr: Адрес строки
            max_len: Максимальная длина

        Returns:
            str или None
        """
        if addr <= 0 or addr > 0x7FFFFFFFFFFF:
            return None

        data = self.read_bytes(addr, max_len)
        if data is None:
            return None

        # Найти null-terminator
        null_idx = data.find(b'\x00')
        if null_idx == 0:
            return ""
        if null_idx >= 0:
            data = data[:null_idx]

        try:
            return data.decode('utf-8', errors='replace')
        except Exception:
            return None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args):
        self.close()


def get_memory_regions(pid: int) -> List[MemoryRegion]:
    """
    Получить список регионов памяти процесса из /proc/pid/maps.

    Args:
        pid: ID процесса

    Returns:
        Список MemoryRegion
    """
    regions = []
    maps_path = f"/proc/{pid}/maps"

    try:
        with open(maps_path, 'r') as f:
            for line in f:
                region = _parse_maps_line(line.strip())
                if region:
                    regions.append(region)
    except (OSError, PermissionError) as e:
        logger.error(f"Ошибка чтения {maps_path}: {e}")

    return regions


def _parse_maps_line(line: str) -> Optional[MemoryRegion]:
    """
    Распарсить строку из /proc/pid/maps.

    Формат: address perms offset dev inode pathname
    Пример: 7f1234000000-7f1234001000 r-xp 00000000 08:01 12345 /path/to/file

    Args:
        line: Строка из maps

    Returns:
        MemoryRegion или None
    """
    if not line:
        return None

    parts = line.split(None, 5)
    if len(parts) < 5:
        return None

    try:
        addr_range = parts[0]
        start_str, end_str = addr_range.split('-')
        start = int(start_str, 16)
        end = int(end_str, 16)

        permissions = parts[1]
        offset = int(parts[2], 16)
        device = parts[3]
        inode = int(parts[4])
        pathname = parts[5] if len(parts) > 5 else ""

        return MemoryRegion(
            start=start,
            end=end,
            permissions=permissions,
            offset=offset,
            device=device,
            inode=inode,
            pathname=pathname.strip()
        )
    except (ValueError, IndexError):
        return None


def find_eve_process() -> Optional[int]:
    """
    Найти процесс EVE Online запущенный через Proton.

    Сканирует /proc/*/cmdline на наличие exefile.exe.
    Через Proton это wine64-preloader + exefile.exe.

    Returns:
        PID процесса или None
    """
    try:
        for entry in os.listdir('/proc'):
            if not entry.isdigit():
                continue

            pid = int(entry)
            cmdline_path = f"/proc/{pid}/cmdline"

            try:
                with open(cmdline_path, 'rb') as f:
                    cmdline = f.read()
            except (OSError, PermissionError):
                continue

            # cmdline содержит аргументы разделённые null-байтами
            cmdline_str = cmdline.decode('utf-8', errors='replace').lower()

            # EVE через Proton: wine64-preloader запускает exefile.exe
            if 'exefile.exe' in cmdline_str:
                logger.info(f"Найден процесс EVE Online: PID {pid}")
                logger.debug(f"cmdline: {cmdline_str[:200]}")
                return pid

    except OSError as e:
        logger.error(f"Ошибка сканирования /proc: {e}")

    return None
