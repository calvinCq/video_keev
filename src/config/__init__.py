"""配置管理模块

负责加载、解析和管理应用配置，支持YAML配置文件和环境变量。
"""

from .manager import ConfigManager, load_config

__all__ = ["ConfigManager", "load_config"]