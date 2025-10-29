"""认证管理模块

负责处理与云端ComfyUI服务的认证相关功能，包括API密钥管理、令牌获取和刷新。
"""

import os
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from ..utils.logger import get_logger

logger = get_logger(__name__)


class AuthManager:
    """认证管理器类
    
    负责管理API认证信息，包括API密钥、访问令牌等。
    """
    
    def __init__(self,
                 api_key: Optional[str] = None,
                 api_endpoint: Optional[str] = None,
                 token_refresh_interval: int = 3600):
        """初始化认证管理器
        
        Args:
            api_key: API密钥，如果为None则尝试从环境变量获取
            api_endpoint: API端点URL
            token_refresh_interval: 令牌刷新间隔（秒）
        """
        self.api_key = api_key or os.getenv('COMFYUI_API_KEY')
        self.api_endpoint = api_endpoint or os.getenv('COMFYUI_API_ENDPOINT')
        self.token_refresh_interval = token_refresh_interval
        
        # 认证相关状态
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        self._last_refresh_time: Optional[datetime] = None
        
        # 检查必要的认证信息
        if not self.api_key:
            logger.warning("未提供API密钥，某些功能可能受限")
    
    def get_auth_headers(self) -> Dict[str, str]:
        """获取认证头信息
        
        Returns:
            包含认证信息的HTTP头字典
        """
        headers = {}
        
        # 优先使用访问令牌
        token = self.get_access_token()
        if token:
            headers['Authorization'] = f'Bearer {token}'
        # 备用方案：直接使用API密钥
        elif self.api_key:
            headers['X-API-Key'] = self.api_key
        
        # 添加用户代理信息
        headers['User-Agent'] = 'VideoKeev-Client/1.0'
        
        return headers
    
    def get_access_token(self) -> Optional[str]:
        """获取访问令牌
        
        如果令牌不存在或即将过期，则尝试刷新令牌。
        
        Returns:
            访问令牌，如果无法获取则返回None
        """
        # 检查令牌是否需要刷新
        if not self._access_token or self._should_refresh_token():
            if not self._refresh_token():
                return None
        
        return self._access_token
    
    def _should_refresh_token(self) -> bool:
        """判断是否需要刷新令牌
        
        Returns:
            如果需要刷新令牌则返回True
        """
        # 如果令牌不存在，则需要刷新
        if not self._access_token:
            return True
        
        # 如果令牌即将过期（剩余时间少于刷新间隔的20%），则需要刷新
        if self._token_expiry:
            time_remaining = (self._token_expiry - datetime.now()).total_seconds()
            return time_remaining < (self.token_refresh_interval * 0.2)
        
        # 如果距离上次刷新时间超过刷新间隔，则需要刷新
        if self._last_refresh_time:
            time_since_refresh = (datetime.now() - self._last_refresh_time).total_seconds()
            return time_since_refresh > self.token_refresh_interval
        
        # 默认需要刷新
        return True
    
    def _refresh_token(self) -> bool:
        """刷新访问令牌
        
        Returns:
            刷新成功则返回True
        """
        try:
            # 注意：这里是模拟实现，实际应该调用云端服务的令牌获取接口
            logger.debug("尝试刷新访问令牌")
            
            # 在实际实现中，这里应该向认证服务器发送请求获取新令牌
            # 例如：
            # import requests
            # response = requests.post(
            #     f"{self.api_endpoint}/auth/token",
            #     json={"api_key": self.api_key},
            #     timeout=30
            # )
            # response.raise_for_status()
            # token_data = response.json()
            # self._access_token = token_data['access_token']
            # expiry_seconds = token_data.get('expires_in', self.token_refresh_interval)
            # self._token_expiry = datetime.now() + timedelta(seconds=expiry_seconds)
            
            # 模拟令牌生成和有效期设置
            self._access_token = self._generate_mock_token()
            self._token_expiry = datetime.now() + timedelta(seconds=self.token_refresh_interval)
            self._last_refresh_time = datetime.now()
            
            logger.info("访问令牌刷新成功")
            return True
        
        except Exception as e:
            logger.error(f"刷新令牌失败: {str(e)}")
            # 出错时清除令牌信息，下次请求时会重新尝试
            self._access_token = None
            self._token_expiry = None
            return False
    
    def _generate_mock_token(self) -> str:
        """生成模拟访问令牌
        
        仅用于开发和测试，生产环境应该使用实际的令牌获取逻辑。
        
        Returns:
            模拟的访问令牌
        """
        import hashlib
        import random
        
        # 生成一个基于时间戳和随机数的模拟令牌
        timestamp = str(int(time.time()))
        random_str = str(random.randint(100000, 999999))
        
        # 使用API密钥（如果有）作为盐值
        salt = self.api_key or 'default_salt'
        
        # 计算哈希值作为令牌的一部分
        hash_input = f"{timestamp}:{random_str}:{salt}"
        hash_value = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
        
        # 构建令牌
        mock_token = f"mock_token_{timestamp}_{hash_value}"
        return mock_token
    
    def is_authenticated(self) -> bool:
        """检查是否已认证
        
        Returns:
            如果已认证则返回True
        """
        # 对于使用API密钥的情况，只要有密钥就认为已认证
        if self.api_key:
            return True
        
        # 对于使用访问令牌的情况，检查令牌是否有效
        token = self.get_access_token()
        return token is not None
    
    def set_api_key(self, api_key: str) -> None:
        """设置API密钥
        
        Args:
            api_key: 新的API密钥
        """
        self.api_key = api_key
        # 重置令牌，下次请求时会使用新的API密钥获取
        self._access_token = None
        self._token_expiry = None
        logger.info("API密钥已更新")
    
    def clear_credentials(self) -> None:
        """清除所有认证凭证"""
        self.api_key = None
        self._access_token = None
        self._token_expiry = None
        self._last_refresh_time = None
        logger.info("所有认证凭证已清除")
    
    def get_auth_info(self) -> Dict[str, Any]:
        """获取认证信息
        
        Returns:
            认证信息字典
        """
        now = datetime.now()
        
        # 计算令牌剩余有效时间
        token_remaining = None
        if self._token_expiry:
            token_remaining = max(0, (self._token_expiry - now).total_seconds())
        
        return {
            'has_api_key': self.api_key is not None,
            'has_access_token': self._access_token is not None,
            'token_expires_at': self._token_expiry.isoformat() if self._token_expiry else None,
            'token_remaining_seconds': token_remaining,
            'last_refresh_time': self._last_refresh_time.isoformat() if self._last_refresh_time else None,
            'is_authenticated': self.is_authenticated()
        }
    
    def save_credentials(self, file_path: str = '.env') -> bool:
        """保存凭证到文件
        
        Args:
            file_path: 保存路径
            
        Returns:
            保存成功则返回True
        """
        try:
            # 读取现有文件内容
            existing_content = []
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_content = f.readlines()
            
            # 更新或添加API密钥
            updated_content = []
            api_key_updated = False
            
            for line in existing_content:
                if line.strip().startswith('COMFYUI_API_KEY='):
                    if self.api_key:
                        updated_content.append(f'COMFYUI_API_KEY={self.api_key}\n')
                        api_key_updated = True
                else:
                    updated_content.append(line)
            
            # 如果没有更新过API密钥且存在API密钥，则添加
            if self.api_key and not api_key_updated:
                updated_content.append(f'COMFYUI_API_KEY={self.api_key}\n')
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(updated_content)
            
            logger.info(f"凭证已保存到 {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存凭证失败: {str(e)}")
            return False