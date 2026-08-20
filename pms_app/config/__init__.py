# Path: pms_app/config/__init__.py
from __future__ import annotations

from typing import Type

from .base import BaseConfig
from .development import DevelopmentConfig
from .production import ProductionConfig

CONFIG_BY_NAME: dict[str, Type[BaseConfig]] = {
    "development": DevelopmentConfig,
    "dev": DevelopmentConfig,
    "production": ProductionConfig,
    "prod": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config(config_name: str | None) -> Type[BaseConfig]:
    key = (config_name or "default").strip().lower()
    return CONFIG_BY_NAME.get(key, DevelopmentConfig)