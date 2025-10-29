"""配置管理器实现

负责加载、解析和验证配置文件，支持YAML格式和环境变量覆盖。
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class ConfigManager:
    """配置管理器类
    
    负责加载、解析和验证配置，支持从文件和环境变量中读取配置。
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """初始化配置管理器
        
        Args:
            config_file: 配置文件路径，如果为None则使用默认配置
        """
        self.config_file = config_file
        self.config = self._load_config()
        self._validate_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置
        
        从配置文件和环境变量加载配置，并进行合并。
        
        Returns:
            合并后的配置字典
        """
        # 默认配置
        default_config = {
            'comfyui': {
                'api_endpoint': os.getenv('COMFYUI_API_ENDPOINT', 'https://api.comfyui-cloud.example/v1'),
                'timeout': int(os.getenv('COMFYUI_TIMEOUT', '300')),
                'retry_count': int(os.getenv('COMFYUI_RETRY_COUNT', '5')),
                'retry_delay': int(os.getenv('COMFYUI_RETRY_DELAY', '5')),
                'upload_chunk_size': int(os.getenv('COMFYUI_CHUNK_SIZE', '5242880'))
            },
            'video': {
                'default_fps': 30,
                'max_resolution': {
                    'width': 1920,
                    'height': 1080
                },
                'temp_dir': './temp',
                'output_dir': './outputs'
            },
            'workflows': {
                'default': {
                    'id': 'default_video_replication',
                    'params': {
                        'model_id': 'realistic_video_v1',
                        'quality_level': 'high'
                    }
                }
            },
            'logging': {
                'level': os.getenv('LOG_LEVEL', 'INFO'),
                'file': os.getenv('LOG_FILE', 'video_keev.log')
            }
        }
        
        # 如果提供了配置文件路径，则加载并合并
        if self.config_file and os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                file_config = yaml.safe_load(f)
                if file_config:
                    # 深度合并配置
                    self._merge_config(default_config, file_config)
        
        # 从环境变量覆盖特定配置
        self._override_from_env(default_config)
        
        return default_config
    
    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """深度合并配置
        
        Args:
            base: 基础配置
            override: 覆盖配置
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def _override_from_env(self, config: Dict[str, Any]) -> None:
        """从环境变量覆盖配置
        
        Args:
            config: 配置字典
        """
        # 已经在默认配置中处理了关键环境变量
        # 这里可以添加更多特定的环境变量覆盖逻辑
        pass
    
    def _validate_config(self) -> None:
        """验证配置有效性
        
        检查配置项是否满足基本要求。
        
        Raises:
            ValueError: 如果配置无效
        """
        # 验证必要的配置项
        if not self.config.get('comfyui', {}).get('api_endpoint'):
            raise ValueError("ComfyUI API端点不能为空")
        
        # 验证超时设置
        timeout = self.config.get('comfyui', {}).get('timeout', 300)
        if not isinstance(timeout, int) or timeout <= 0:
            raise ValueError("超时设置必须是正整数")
        
        # 验证重试设置
        retry_count = self.config.get('comfyui', {}).get('retry_count', 5)
        if not isinstance(retry_count, int) or retry_count < 0:
            raise ValueError("重试次数必须是非负整数")
        
        # 验证目录配置
        temp_dir = self.config.get('video', {}).get('temp_dir', './temp')
        output_dir = self.config.get('video', {}).get('output_dir', './outputs')
        
        # 确保目录存在
        Path(temp_dir).mkdir(parents=True, exist_ok=True)
        Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项
        
        Args:
            key: 配置键，支持使用点号访问嵌套配置
            default: 默认值
            
        Returns:
            配置值或默认值
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def update(self, key: str, value: Any) -> None:
        """更新配置项
        
        Args:
            key: 配置键，支持使用点号访问嵌套配置
            value: 新值
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self._validate_config()
    
    def to_dict(self) -> Dict[str, Any]:
        """获取完整配置字典
        
        Returns:
            完整的配置字典
        """
        return self.config.copy()
    
    def save(self, file_path: Optional[str] = None) -> None:
        """保存配置到文件
        
        Args:
            file_path: 保存路径，如果为None则使用初始化时的路径
        """
        path = file_path or self.config_file
        if not path:
            raise ValueError("未指定保存路径")
        
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)


def load_config(config_file: Optional[str] = None) -> ConfigManager:
    """加载配置
    
    工厂函数，创建并返回配置管理器实例。
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        配置管理器实例
    """
    return ConfigManager(config_file)