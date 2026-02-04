"""Root address caching for fast Sanderling startup."""
import json
import os
import time
from dataclasses import dataclass, asdict
from typing import Optional
from pathlib import Path


@dataclass
class CacheEntry:
    """Запись в кэше root address."""
    root_address: str
    process_id: int
    timestamp: float
    game_version: Optional[str] = None


class RootAddressCache:
    """Кэш для хранения root address UI tree."""
    
    def __init__(self, cache_file: str = "output/data/sanderling_cache.json"):
        """
        Инициализация кэша.
        
        Args:
            cache_file: Путь к файлу кэша
        """
        self.cache_file = cache_file
        self.data = self._load()
        
    def get(self, process_id: int) -> Optional[str]:
        """
        Получить root address для процесса.
        
        Args:
            process_id: ID процесса EVE
            
        Returns:
            Root address или None если не найден
        """
        key = str(process_id)
        if key not in self.data:
            return None
            
        entry = self.data[key]
        if not self._is_valid(entry):
            self.invalidate(process_id)
            return None
            
        return entry.get('root_address')
        
    def set(self, process_id: int, root_address: str, game_version: Optional[str] = None) -> None:
        """
        Сохранить root address.
        
        Args:
            process_id: ID процесса EVE
            root_address: Адрес UI root
            game_version: Версия игры (опционально)
        """
        entry = CacheEntry(
            root_address=root_address,
            process_id=process_id,
            timestamp=time.time(),
            game_version=game_version
        )
        self.data[str(process_id)] = asdict(entry)
        self._save()
        
    def invalidate(self, process_id: int) -> None:
        """
        Инвалидировать кэш для процесса.
        
        Args:
            process_id: ID процесса EVE
        """
        key = str(process_id)
        if key in self.data:
            del self.data[key]
            self._save()
        
    def _load(self) -> dict:
        """Загрузить кэш из файла."""
        if not os.path.exists(self.cache_file):
            return {}
            
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
        
    def _save(self) -> None:
        """Сохранить кэш в файл."""
        # Создать директорию если не существует
        Path(self.cache_file).parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Warning: Failed to save cache: {e}")
        
    def _is_valid(self, entry: dict) -> bool:
        """
        Проверить валидность записи кэша.
        
        Args:
            entry: Запись кэша
            
        Returns:
            True если запись валидна
        """
        if not isinstance(entry, dict):
            return False
            
        # Проверить наличие обязательных полей
        if 'root_address' not in entry or 'timestamp' not in entry:
            return False
            
        # Проверить что запись не старше 24 часов
        age_hours = (time.time() - entry['timestamp']) / 3600
        if age_hours > 24:
            return False
            
        return True
