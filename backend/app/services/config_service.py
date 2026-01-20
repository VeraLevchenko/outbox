import json
import os
from pathlib import Path
from typing import Dict, List, Optional


class ConfigService:
    """Сервис для работы с конфигурационными JSON файлами"""

    def __init__(self):
        self.config_dir = Path(__file__).parent.parent.parent / "config"
        self.executors_file = self.config_dir / "executors.json"
        self.numbering_rules_file = self.config_dir / "numbering_rules.json"
        self._executors_cache = None
        self._numbering_rules_cache = None

    def _load_json(self, file_path: Path) -> Dict:
        """Загрузить JSON файл"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Config file not found: {file_path}")
            return {}
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON from {file_path}: {e}")
            return {}

    def get_executors(self) -> List[Dict]:
        """
        Получить список исполнителей из конфигурации

        Returns:
            Список исполнителей с их данными
        """
        if self._executors_cache is None:
            config = self._load_json(self.executors_file)
            self._executors_cache = config.get('executors', [])
        return self._executors_cache

    def get_executor_by_user_id(self, user_id: int) -> Optional[Dict]:
        """
        Получить данные исполнителя по user_id

        Args:
            user_id: ID пользователя из Kaiten

        Returns:
            Данные исполнителя или None если не найден
        """
        executors = self.get_executors()
        for executor in executors:
            if executor.get('user_id') == user_id:
                return executor
        return None

    def get_numbering_rules(self) -> Dict:
        """
        Получить правила нумерации

        Returns:
            Словарь с правилами нумерации
        """
        if self._numbering_rules_cache is None:
            config = self._load_json(self.numbering_rules_file)
            self._numbering_rules_cache = config.get('rules', {})
        return self._numbering_rules_cache

    def get_numbering_rule_for_executor(self, user_id: int) -> Dict:
        """
        Получить правило нумерации для конкретного исполнителя

        Args:
            user_id: ID пользователя из Kaiten

        Returns:
            Правило нумерации для этого исполнителя или правило по умолчанию
        """
        rules = self.get_numbering_rules()
        user_id_str = str(user_id)

        if user_id_str in rules:
            return rules[user_id_str]

        # Возвращаем правило по умолчанию
        return rules.get('default', {
            'prefix': 'ОБЩ',
            'format': '{number}',
            'start_number': 1,
            'reset_yearly': False
        })

    def reload_configs(self):
        """Перезагрузить конфигурации из файлов (для быстрых изменений)"""
        self._executors_cache = None
        self._numbering_rules_cache = None
        print("Configuration files reloaded")


# Singleton instance
config_service = ConfigService()
