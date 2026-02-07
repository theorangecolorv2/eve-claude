"""Sanderling background service for EVE Online memory reading."""
import subprocess
import sys
import json
import time
import psutil
import threading
import logging
from typing import Optional
from pathlib import Path

from .config import SanderlingConfig
from .cache import RootAddressCache
from .parser import UITreeParser
from .models import GameState


logger = logging.getLogger(__name__)


class SanderlingService:
    """Фоновый сервис для чтения памяти EVE Online через Sanderling."""
    
    def __init__(self, config: Optional[SanderlingConfig] = None):
        """
        Инициализация сервиса.
        
        Args:
            config: Конфигурация Sanderling (если None, загружается из файла)
        """
        self.config = config or SanderlingConfig.load()
        self.cache = RootAddressCache() if self.config.cache_enabled else None
        self.parser = UITreeParser()
        
        self.process_handle = None
        self.eve_process_id = None
        self.is_running = False
        self.last_state = None
        self.last_ui_tree = None  # Добавляем хранение последнего UI tree
        self.error_count = 0
        self.error_timestamps = []
        
        self._thread = None
        self._stop_event = threading.Event()
        self._root_address = None
        self._read_count = 0
        self._last_read_time_ms = 0
        self._state_lock = threading.Lock()  # Защита от race condition
        
    def start(self) -> bool:
        """
        Запустить сервис.
        
        Returns:
            True если запуск успешен, False иначе
        """
        if not self.config.enabled:
            logger.info("Sanderling is disabled in config")
            return False
        
        if self.is_running:
            logger.warning("Service is already running")
            return True
        
        logger.info("Starting Sanderling service...")
        
        # Найти процесс EVE
        self.eve_process_id = self._find_eve_process()
        if not self.eve_process_id:
            logger.error("EVE Online process not found")
            return False
        
        logger.info(f"Found EVE process: {self.eve_process_id}")
        
        # Загрузить root address из кэша
        if self.cache:
            self._root_address = self.cache.get(self.eve_process_id)
            if self._root_address:
                logger.info(f"Loaded root address from cache: {self._root_address}")
        
        # Если нет в кэше, выполнить полный поиск
        if not self._root_address:
            logger.info("Root address not in cache, performing full search...")
            self._root_address = self._find_root_address()
            if not self._root_address:
                logger.error("Failed to find root address")
                return False
            
            # Сохранить в кэш
            if self.cache:
                self.cache.set(self.eve_process_id, self._root_address)
                logger.info("Root address cached")
        
        # Запустить фоновый поток чтения
        self.is_running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()
        
        logger.info("Service started")
        return True
        
    def stop(self) -> None:
        """Остановить сервис."""
        if not self.is_running:
            return
        
        logger.info("Stopping service...")
        
        self.is_running = False
        self._stop_event.set()
        
        if self._thread:
            self._thread.join(timeout=5.0)
        
        if self.process_handle:
            try:
                self.process_handle.terminate()
                self.process_handle.wait(timeout=3.0)
            except:
                pass
        
        logger.info("Service stopped")
        
    def get_state(self) -> Optional[GameState]:
        """
        Получить текущее состояние игры (thread-safe).
        
        Returns:
            GameState или None если данные недоступны
        """
        with self._state_lock:
            return self.last_state
    
    def get_ui_tree(self) -> Optional[dict]:
        """
        Получить последний сырой UI tree (thread-safe).
        
        Returns:
            UI tree dict или None если данные недоступны
        """
        with self._state_lock:
            return self.last_ui_tree
    
    # Properties для удобного доступа к данным
    @property
    def read_count(self) -> int:
        """Количество успешных чтений."""
        return getattr(self, '_read_count', 0)
    
    @property
    def last_read_time_ms(self) -> int:
        """Время последнего чтения в миллисекундах."""
        return getattr(self, '_last_read_time_ms', 0)
    
    @property
    def targets(self):
        """Список целей (thread-safe)."""
        with self._state_lock:
            return self.last_state.targets if self.last_state else []
    
    @property
    def targets_count(self) -> int:
        """Количество целей."""
        return len(self.targets)
    
    @property
    def overview(self):
        """Список записей overview (thread-safe)."""
        with self._state_lock:
            return self.last_state.overview if self.last_state else []
    
    @property
    def overview_count(self) -> int:
        """Количество записей в overview."""
        return len(self.overview)
    
    @property
    def modules(self):
        """Список модулей (thread-safe)."""
        with self._state_lock:
            return self.last_state.ship.modules if self.last_state and self.last_state.ship else []
    
    @property
    def active_modules_count(self) -> int:
        """Количество активных модулей."""
        return sum(1 for m in self.modules if m.is_active)
        
    def _find_eve_process(self) -> Optional[int]:
        """
        Найти процесс EVE Online.

        На Windows: ищем exefile.exe через psutil.
        На Linux: ищем через /proc/*/cmdline (EVE через Proton).

        Returns:
            Process ID или None
        """
        max_attempts = 12  # 12 * 5 секунд = 1 минута
        attempt = 0

        while attempt < max_attempts:
            # Linux: используем специализированный поиск через /proc
            if sys.platform == 'linux':
                from .linux_process import find_eve_process
                pid = find_eve_process()
                if pid:
                    return pid
            else:
                # Windows: стандартный поиск через psutil
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        if proc.info['name'].lower() == 'exefile.exe':
                            return proc.info['pid']
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

            if attempt < max_attempts - 1:
                logger.debug(f"EVE process not found, waiting... (attempt {attempt + 1}/{max_attempts})")
                time.sleep(5.0)

            attempt += 1

        return None
        
    def _find_root_address(self) -> Optional[str]:
        """
        Найти root address через полный поиск.

        На Windows: запускает read-memory-64-bit.exe.
        На Linux: использует LinuxMemoryReader напрямую.

        Returns:
            Root address или None
        """
        # Linux: используем LinuxMemoryReader напрямую (без subprocess)
        if sys.platform == 'linux':
            return self._find_root_address_linux()

        # Windows: запускаем C# exe
        if not Path(self.config.binary_path).exists():
            logger.error(f"Sanderling binary not found: {self.config.binary_path}")
            return None

        try:
            cmd = [
                self.config.binary_path,
                "read-memory-eve-online",
                f"--pid={self.eve_process_id}",
                "--remove-other-dict-entries"
            ]

            logger.info("Searching for root address (may take up to 3 minutes)...")
            start_time = time.time()

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180.0
            )

            elapsed = time.time() - start_time
            logger.info(f"Search completed in {elapsed:.1f}s")

            if result.returncode != 0:
                logger.error(f"Sanderling failed with exit code {result.returncode}")
                logger.error(f"STDERR: {result.stderr}")
                return None

            output = result.stdout
            logger.debug(f"Sanderling output: {output}")

            import re
            matches = re.findall(r'(0x[0-9A-Fa-f]+):\s+(\d+)\s+nodes', output)

            if not matches:
                logger.error("Could not find root address in output")
                return None

            root_address = max(matches, key=lambda x: int(x[1]))[0]
            logger.info(f"Found root address: {root_address}")

            try:
                match = re.search(r"to file '([^']+)'", output)
                if match:
                    json_file = Path(match.group(1))
                    if json_file.exists():
                        json_file.unlink()
            except Exception:
                pass

            return root_address

        except subprocess.TimeoutExpired:
            logger.error("Root address search timed out (180s)")
            return None
        except Exception as e:
            logger.error(f"Error finding root address: {e}")
            return None

    def _find_root_address_linux(self) -> Optional[str]:
        """Найти root address на Linux через LinuxMemoryReader."""
        from .linux_reader import LinuxMemoryReader
        try:
            reader = LinuxMemoryReader(
                self.eve_process_id,
                scan_chunk_size=self.config.linux_scan_chunk_size
            )
            if not reader.open():
                logger.error("Не удалось открыть доступ к памяти процесса")
                return None

            try:
                root = reader.find_root_address()
                return root
            finally:
                reader.close()
        except Exception as e:
            logger.error(f"Ошибка поиска root address на Linux: {e}")
            return None
        
    def _read_memory(self) -> Optional[dict]:
        """
        Прочитать память и вернуть UI tree.

        На Windows: subprocess → C# exe → JSON файл.
        На Linux: LinuxMemoryReader напрямую → dict.

        Returns:
            UI tree dict или None
        """
        # Linux: читаем память напрямую из Python (без subprocess!)
        if sys.platform == 'linux':
            return self._read_memory_linux()

        # Windows: стандартный путь через C# exe
        if not Path(self.config.binary_path).exists():
            return None

        try:
            if Path("R:/").exists():
                temp_dir = Path("R:/temp")
            else:
                temp_dir = Path("temp")
            temp_dir.mkdir(exist_ok=True)

            cmd = [
                str(Path(self.config.binary_path).absolute()),
                "read-memory-eve-online",
                f"--pid={self.eve_process_id}",
                "--remove-other-dict-entries"
            ]

            if self._root_address:
                cmd.extend(["--root-address", self._root_address])

            start_time = time.time()

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(temp_dir.absolute()),
                timeout=self.config.timeout_ms / 1000.0
            )

            elapsed_ms = (time.time() - start_time) * 1000

            if result.returncode != 0:
                logger.error(f"Sanderling read failed with exit code {result.returncode}")
                return None

            output = result.stdout

            import re
            match = re.search(r"to file '([^']+)'", output)

            if not match:
                logger.error("Could not find output file path in Sanderling output")
                logger.debug(f"Output: {output}")
                return None

            json_filename = Path(match.group(1)).name
            json_file = temp_dir / json_filename

            if not json_file.exists():
                logger.error(f"JSON file not found: {json_file}")
                return None

            with open(json_file, 'r', encoding='utf-8') as f:
                ui_tree = json.load(f)

            try:
                json_file.unlink()
            except Exception:
                pass

            if self.config.debug_mode:
                self._save_debug_snapshot(ui_tree)

            return ui_tree

        except subprocess.TimeoutExpired:
            logger.error("Memory read timed out")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse UI tree JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Error reading memory: {e}")
            return None

    def _read_memory_linux(self) -> Optional[dict]:
        """Прочитать UI tree на Linux через LinuxMemoryReader."""
        from .linux_reader import LinuxMemoryReader
        try:
            reader = LinuxMemoryReader(
                self.eve_process_id,
                scan_chunk_size=self.config.linux_scan_chunk_size
            )
            if not reader.open():
                logger.error("Не удалось открыть доступ к памяти")
                return None

            try:
                ui_tree = reader.read_ui_tree(self._root_address)

                if self.config.debug_mode and ui_tree:
                    self._save_debug_snapshot(ui_tree)

                return ui_tree
            finally:
                reader.close()
        except Exception as e:
            logger.error(f"Ошибка чтения памяти на Linux: {e}")
            return None
        
    def _read_loop(self) -> None:
        """Фоновый цикл чтения памяти."""
        logger.debug("Read loop started")
        
        while not self._stop_event.is_set():
            try:
                # Проверить что процесс EVE еще жив
                if not self._is_eve_running():
                    logger.warning("EVE process terminated")
                    self.is_running = False
                    break
                
                # Читать память
                start_time = time.time()
                ui_tree = self._read_memory()
                read_time_ms = int((time.time() - start_time) * 1000)
                
                if ui_tree:
                    # Парсить UI tree
                    state = self.parser.parse(ui_tree)
                    
                    # Thread-safe обновление состояния
                    with self._state_lock:
                        self.last_state = state
                        self.last_ui_tree = ui_tree  # Сохраняем сырой UI tree
                    
                    self.error_count = 0
                    self._read_count += 1
                    self._last_read_time_ms = read_time_ms
                else:
                    self._handle_error(Exception("Failed to read memory"))
                
            except Exception as e:
                self._handle_error(e)
            
            # Ждать перед следующим чтением
            time.sleep(self.config.read_interval_ms / 1000.0)
        
        logger.debug("Read loop stopped")
        
    def _handle_error(self, error: Exception) -> None:
        """
        Обработать ошибку чтения.
        
        Args:
            error: Исключение
        """
        self.error_count += 1
        self.error_timestamps.append(time.time())
        
        logger.error(f"Read error (count: {self.error_count}): {error}")
        
        # Проверить частоту ошибок (более 10 за 5 минут)
        recent_errors = [t for t in self.error_timestamps if time.time() - t < 300]
        if len(recent_errors) > 10:
            logger.warning(f"High error rate: {len(recent_errors)} errors in 5 min")
        
        # Retry механизм
        if self.error_count >= self.config.max_retries:
            logger.warning("Max retries reached, searching for new root address")
            
            # Инвалидировать кэш
            if self.cache and self.eve_process_id:
                self.cache.invalidate(self.eve_process_id)
            
            # Выполнить полный поиск
            self._root_address = self._find_root_address()
            
            if self._root_address and self.cache and self.eve_process_id:
                self.cache.set(self.eve_process_id, self._root_address)
                logger.info("Root address updated")
            
            self.error_count = 0
        else:
            # Подождать перед повтором
            time.sleep(1.0)
        
    def _is_eve_running(self) -> bool:
        """
        Проверить что процесс EVE еще работает.
        
        Returns:
            True если процесс жив
        """
        if not self.eve_process_id:
            return False
        
        try:
            proc = psutil.Process(self.eve_process_id)
            return proc.is_running()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
        
    def _save_debug_snapshot(self, ui_tree: dict) -> None:
        """
        Сохранить снимок UI tree в debug режиме.
        
        Args:
            ui_tree: UI tree для сохранения
        """
        try:
            timestamp = time.strftime("%H%M%S")
            filename = f"output/debug/ui_tree_{timestamp}.json"
            
            Path(filename).parent.mkdir(parents=True, exist_ok=True)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(ui_tree, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Failed to save debug snapshot: {e}")
