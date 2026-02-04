"""Sanderling configuration management."""
import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


@dataclass
class SanderlingConfig:
    """Конфигурация Sanderling."""
    
    enabled: bool = True
    fallback_to_cv: bool = True
    cache_enabled: bool = True
    read_interval_ms: int = 1000  # 1 секунда
    max_retries: int = 3
    timeout_ms: int = 5000
    binary_path: str = "external/sanderling-bin/read-memory-64-bit.exe"
    debug_mode: bool = False
    
    @classmethod
    def load(cls, config_file: str = "resources/config/sanderling.json") -> "SanderlingConfig":
        """
        Загрузить конфигурацию из файла.
        
        Args:
            config_file: Путь к файлу конфигурации
            
        Returns:
            SanderlingConfig с загруженными настройками
        """
        if not os.path.exists(config_file):
            print(f"Warning: Config file {config_file} not found, using defaults")
            return cls()
            
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            config = cls(**data)
            
            if not config.validate():
                print("Warning: Invalid config values, using defaults where needed")
                
            return config
            
        except (json.JSONDecodeError, TypeError, IOError) as e:
            print(f"Warning: Failed to load config: {e}, using defaults")
            return cls()
        
    def save(self, config_file: str = "resources/config/sanderling.json") -> None:
        """
        Сохранить конфигурацию в файл.
        
        Args:
            config_file: Путь к файлу конфигурации
        """
        # Создать директорию если не существует
        Path(config_file).parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self), f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Warning: Failed to save config: {e}")
        
    def validate(self) -> bool:
        """
        Валидировать значения конфигурации.
        
        Returns:
            True если все значения валидны
        """
        valid = True
        
        # Валидация типов
        if not isinstance(self.enabled, bool):
            print("Warning: 'enabled' must be bool")
            self.enabled = True
            valid = False
            
        if not isinstance(self.fallback_to_cv, bool):
            print("Warning: 'fallback_to_cv' must be bool")
            self.fallback_to_cv = True
            valid = False
            
        if not isinstance(self.cache_enabled, bool):
            print("Warning: 'cache_enabled' must be bool")
            self.cache_enabled = True
            valid = False
            
        if not isinstance(self.debug_mode, bool):
            print("Warning: 'debug_mode' must be bool")
            self.debug_mode = False
            valid = False
            
        # Валидация диапазонов
        if not isinstance(self.read_interval_ms, int) or self.read_interval_ms < 50 or self.read_interval_ms > 5000:
            print("Warning: 'read_interval_ms' must be int between 50 and 5000")
            self.read_interval_ms = 200
            valid = False
            
        if not isinstance(self.max_retries, int) or self.max_retries < 1 or self.max_retries > 10:
            print("Warning: 'max_retries' must be int between 1 and 10")
            self.max_retries = 3
            valid = False
            
        if not isinstance(self.timeout_ms, int) or self.timeout_ms < 1000 or self.timeout_ms > 30000:
            print("Warning: 'timeout_ms' must be int between 1000 and 30000")
            self.timeout_ms = 5000
            valid = False
            
        if not isinstance(self.binary_path, str) or not self.binary_path:
            print("Warning: 'binary_path' must be non-empty string")
            self.binary_path = "external/sanderling-bin/read-memory-64-bit.exe"
            valid = False
            
        return valid
