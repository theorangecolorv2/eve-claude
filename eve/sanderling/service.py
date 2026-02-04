# eve/sanderling/service.py
"""
Sanderling Service - фоновое чтение памяти EVE Online.

Запускает фоновый поток, который периодически читает память
и предоставляет актуальные данные о состоянии игры.
"""

import json
import logging
import subprocess
import threading
import time
import re
from pathlib import Path
from typing import Optional, List

from .models import Target, OverviewEntry, Module, ShipState, GameState
from .parser import UITreeParser

logger = logging.getLogger(__name__)


class SanderlingService:
    """
    Сервис чтения памяти EVE Online.

    Использование:
        service = SanderlingService()
        service.start()

        # Получить данные
        print(f"Targets: {service.targets_count}")
        print(f"Overview: {service.overview_count}")

        for target in service.targets:
            print(f"  - {target.name} at {target.distance}")

        service.stop()
    """

    # Путь к read-memory-64-bit.exe (относительно корня проекта)
    DEFAULT_EXE_PATH = Path(__file__).parent.parent.parent / "sanderling-bin" / "read-memory-64-bit.exe"

    def __init__(
        self,
        exe_path: Optional[Path] = None,
        update_interval: float = 0.3,
        auto_find_process: bool = True
    ):
        """
        Инициализация сервиса.

        Args:
            exe_path: Путь к read-memory-64-bit.exe
            update_interval: Интервал обновления в секундах (по умолчанию 0.3)
            auto_find_process: Автоматически найти процесс EVE Online
        """
        self.exe_path = Path(exe_path) if exe_path else self.DEFAULT_EXE_PATH
        self.update_interval = update_interval
        self.auto_find_process = auto_find_process

        # Состояние
        self._state: Optional[GameState] = None
        self._lock = threading.RLock()
        self._running = False
        self._thread: Optional[threading.Thread] = None

        # Процесс EVE
        self._process_id: Optional[int] = None
        self._root_address: Optional[str] = None

        # Статистика
        self._read_count = 0
        self._error_count = 0
        self._last_error: Optional[str] = None
        self._last_read_time_ms = 0

    # =========== LIFECYCLE ===========

    def start(self, process_id: Optional[int] = None, root_address: Optional[str] = None) -> bool:
        """
        Запустить сервис.

        Args:
            process_id: ID процесса EVE Online (если не указан, найдёт автоматически)
            root_address: Адрес UI root (если не указан, будет искать ~20 сек)

        Returns:
            True если успешно запущен
        """
        if self._running:
            logger.warning("Сервис уже запущен")
            return True

        # Проверяем exe
        if not self.exe_path.exists():
            logger.error(f"Не найден {self.exe_path}")
            return False

        # Находим процесс EVE
        if process_id:
            self._process_id = process_id
        elif self.auto_find_process:
            self._process_id = self._find_eve_process()
            if not self._process_id:
                logger.error("Не найден процесс EVE Online")
                return False
        else:
            logger.error("Не указан process_id")
            return False

        logger.info(f"Найден процесс EVE Online: PID={self._process_id}")

        # Используем указанный root address или ищем
        if root_address:
            self._root_address = root_address
            logger.info(f"Используем указанный UI root: {self._root_address}")
        else:
            # Находим UI root address (медленная операция)
            logger.info("Поиск UI root address (это может занять ~20 секунд)...")
            self._root_address = self._find_root_address()
            if not self._root_address:
                logger.error("Не найден UI root address")
                return False
            logger.info(f"Найден UI root: {self._root_address}")

        # Запускаем фоновый поток
        self._running = True
        self._thread = threading.Thread(target=self._reader_loop, daemon=True)
        self._thread.start()

        logger.info("Sanderling сервис запущен")
        return True

    def stop(self):
        """Остановить сервис."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        logger.info("Sanderling сервис остановлен")

    def is_running(self) -> bool:
        """Проверить, запущен ли сервис."""
        return self._running

    # =========== DATA ACCESS ===========

    @property
    def state(self) -> Optional[GameState]:
        """Полное состояние игры."""
        with self._lock:
            return self._state

    @property
    def targets(self) -> List[Target]:
        """Список залоченных целей."""
        with self._lock:
            if self._state:
                return self._state.targets.copy()
            return []

    @property
    def targets_count(self) -> int:
        """Количество залоченных целей."""
        with self._lock:
            if self._state:
                return len(self._state.targets)
            return 0

    @property
    def active_target(self) -> Optional[Target]:
        """Текущая активная цель."""
        with self._lock:
            if self._state:
                return self._state.active_target
            return None

    @property
    def overview(self) -> List[OverviewEntry]:
        """Список записей Overview."""
        with self._lock:
            if self._state:
                return self._state.overview.copy()
            return []

    @property
    def overview_count(self) -> int:
        """Количество записей в Overview."""
        with self._lock:
            if self._state:
                return len(self._state.overview)
            return 0

    @property
    def ship(self) -> Optional[ShipState]:
        """Состояние корабля."""
        with self._lock:
            if self._state:
                return self._state.ship
            return None

    @property
    def modules(self) -> List[Module]:
        """Список модулей корабля."""
        with self._lock:
            if self._state and self._state.ship:
                return self._state.ship.modules.copy()
            return []

    @property
    def active_modules_count(self) -> int:
        """Количество активных модулей."""
        with self._lock:
            if self._state and self._state.ship:
                return self._state.ship.active_modules_count
            return 0

    # =========== STATS ===========

    @property
    def read_count(self) -> int:
        """Количество успешных чтений."""
        return self._read_count

    @property
    def error_count(self) -> int:
        """Количество ошибок."""
        return self._error_count

    @property
    def last_error(self) -> Optional[str]:
        """Последняя ошибка."""
        return self._last_error

    @property
    def last_read_time_ms(self) -> int:
        """Время последнего чтения в миллисекундах."""
        return self._last_read_time_ms

    # =========== INTERNAL ===========

    def _find_eve_process(self) -> Optional[int]:
        """Найти процесс EVE Online."""
        try:
            # Используем PowerShell для поиска процесса
            result = subprocess.run(
                ['powershell', '-Command',
                 'Get-Process exefile -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                return int(result.stdout.strip().split()[0])
        except Exception as e:
            logger.error(f"Ошибка поиска процесса EVE: {e}")
        return None

    def _find_root_address(self) -> Optional[str]:
        """Найти UI root address (медленная операция)."""
        try:
            result = subprocess.run(
                [str(self.exe_path), 'read-memory-eve-online',
                 f'--pid={self._process_id}',
                 '--remove-other-dict-entries'],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                # Парсим вывод: "Read 1 UI trees in 164 milliseconds:\n0x276A59E2CF8: 1316 nodes."
                match = re.search(r'(0x[0-9A-Fa-f]+):\s*\d+\s*nodes', result.stdout)
                if match:
                    return match.group(1)

            logger.error(f"Не удалось найти root address: {result.stderr}")
        except subprocess.TimeoutExpired:
            logger.error("Таймаут при поиске root address")
        except Exception as e:
            logger.error(f"Ошибка поиска root address: {e}")

        return None

    def _reader_loop(self):
        """Основной цикл чтения памяти."""
        while self._running:
            try:
                start_time = time.time()

                # Читаем память
                json_data = self._read_memory()

                if json_data:
                    # Парсим
                    parser = UITreeParser(json_data)
                    state = parser.parse()

                    # Добавляем метаданные
                    state.timestamp = time.time()
                    state.read_time_ms = self._last_read_time_ms

                    # Сохраняем
                    with self._lock:
                        self._state = state

                    self._read_count += 1
                else:
                    self._error_count += 1

                # Ждём до следующего чтения
                elapsed = time.time() - start_time
                sleep_time = max(0, self.update_interval - elapsed)
                time.sleep(sleep_time)

            except Exception as e:
                logger.exception(f"Ошибка в reader loop: {e}")
                self._error_count += 1
                self._last_error = str(e)
                time.sleep(1)  # Пауза при ошибке

    def _read_memory(self) -> Optional[dict]:
        """Прочитать память и вернуть JSON."""
        try:
            start = time.time()

            # Запускаем read-memory-64-bit и читаем stdout
            result = subprocess.run(
                [str(self.exe_path), 'read-memory-eve-online',
                 f'--pid={self._process_id}',
                 f'--root-address={self._root_address}',
                 '--remove-other-dict-entries',
                 '--output-file=-'],  # '-' означает stdout
                capture_output=True,
                text=True,
                timeout=10
            )

            self._last_read_time_ms = int((time.time() - start) * 1000)

            # К сожалению, read-memory-64-bit не поддерживает вывод в stdout
            # Нужно использовать временный файл или именованный pipe
            # Пока используем временный файл
            return self._read_memory_via_file()

        except subprocess.TimeoutExpired:
            logger.error("Таймаут при чтении памяти")
            self._last_error = "Timeout"
        except Exception as e:
            logger.error(f"Ошибка чтения памяти: {e}")
            self._last_error = str(e)

        return None

    def _read_memory_via_file(self) -> Optional[dict]:
        """Прочитать память через временный файл."""
        import tempfile
        import os

        try:
            start = time.time()

            # Создаём временный файл
            fd, temp_path = tempfile.mkstemp(suffix='.json')
            os.close(fd)

            try:
                # Запускаем чтение
                result = subprocess.run(
                    [str(self.exe_path), 'read-memory-eve-online',
                     f'--pid={self._process_id}',
                     f'--root-address={self._root_address}',
                     '--remove-other-dict-entries',
                     f'--output-file={temp_path}'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                self._last_read_time_ms = int((time.time() - start) * 1000)

                if result.returncode == 0 and Path(temp_path).exists():
                    with open(temp_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                else:
                    logger.error(f"Ошибка чтения: {result.stderr}")
                    self._last_error = result.stderr

            finally:
                # Удаляем временный файл
                try:
                    os.unlink(temp_path)
                except:
                    pass

        except subprocess.TimeoutExpired:
            logger.error("Таймаут при чтении памяти")
            self._last_error = "Timeout"
        except Exception as e:
            logger.error(f"Ошибка чтения памяти: {e}")
            self._last_error = str(e)

        return None


# Глобальный экземпляр для удобства
_default_service: Optional[SanderlingService] = None


def get_service() -> SanderlingService:
    """Получить глобальный экземпляр сервиса."""
    global _default_service
    if _default_service is None:
        _default_service = SanderlingService()
    return _default_service


def start_service(**kwargs) -> bool:
    """Запустить глобальный сервис."""
    return get_service().start(**kwargs)


def stop_service():
    """Остановить глобальный сервис."""
    global _default_service
    if _default_service:
        _default_service.stop()
        _default_service = None
