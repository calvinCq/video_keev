"""HTTP客户端模块

提供与云端ComfyUI服务通信的HTTP客户端功能，包括请求发送、错误重试和文件上传下载。
"""

import time
import json
import requests
from typing import Optional, Dict, Any, Union, BinaryIO, Iterator, List, Tuple, IO
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..utils.logger import get_logger
from .auth import AuthManager

logger = get_logger(__name__)


class HttpClient:
    """HTTP客户端类
    
    封装与云端服务的HTTP通信，支持重试机制和文件上传下载。
    """
    
    def __init__(self,
                 base_url: str,
                 auth_manager: Optional[AuthManager] = None,
                 timeout: int = 30,
                 retry_count: int = 5,
                 retry_delay: int = 5,
                 chunk_size: int = 5 * 1024 * 1024):  # 5MB
        """初始化HTTP客户端
        
        Args:
            base_url: API基础URL
            auth_manager: 认证管理器实例
            timeout: 请求超时时间（秒）
            retry_count: 最大重试次数
            retry_delay: 重试间隔（秒）
            chunk_size: 文件上传/下载的块大小
        """
        self.base_url = base_url.rstrip('/')
        self.auth_manager = auth_manager
        self.timeout = timeout
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.chunk_size = chunk_size
        
        # 创建会话
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """创建并配置会话
        
        Returns:
            配置好的requests会话
        """
        session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=self.retry_count,
            backoff_factor=self.retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # 设置默认超时
        session.timeout = self.timeout
        
        return session
    
    def _prepare_request(self, method: str, path: str, **kwargs) -> requests.Request:
        """准备请求
        
        Args:
            method: HTTP方法
            path: API路径
            **kwargs: 其他请求参数
            
        Returns:
            准备好的请求对象
        """
        # 构建完整URL
        url = f"{self.base_url}/{path.lstrip('/')}"
        
        # 获取认证头
        headers = kwargs.get('headers', {})
        if self.auth_manager:
            auth_headers = self.auth_manager.get_auth_headers()
            headers.update(auth_headers)
        
        # 添加Content-Type（如果是JSON请求且未指定）
        if method in ['POST', 'PUT'] and 'json' in kwargs and 'Content-Type' not in headers:
            headers['Content-Type'] = 'application/json'
        
        kwargs['headers'] = headers
        
        # 创建请求
        return requests.Request(method, url, **kwargs)
    
    def _send_request(self, request: requests.Request) -> requests.Response:
        """发送请求
        
        Args:
            request: 请求对象
            
        Returns:
            响应对象
            
        Raises:
            requests.HTTPError: 如果请求失败
        """
        prepared_request = self.session.prepare_request(request)
        
        logger.debug(f"发送请求: {request.method} {prepared_request.url}")
        
        try:
            response = self.session.send(prepared_request)
            
            # 检查响应状态
            response.raise_for_status()
            
            logger.debug(f"请求成功: {request.method} {prepared_request.url} - 状态码: {response.status_code}")
            return response
            
        except requests.HTTPError as e:
            logger.error(f"HTTP错误: {str(e)} - {request.method} {prepared_request.url}")
            raise
        except requests.ConnectionError as e:
            logger.error(f"连接错误: {str(e)} - {request.method} {prepared_request.url}")
            raise
        except requests.Timeout as e:
            logger.error(f"请求超时: {str(e)} - {request.method} {prepared_request.url}")
            raise
        except Exception as e:
            logger.error(f"请求异常: {str(e)} - {request.method} {prepared_request.url}")
            raise
    
    def request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """发送HTTP请求并返回JSON响应
        
        Args:
            method: HTTP方法
            path: API路径
            **kwargs: 其他请求参数
            
        Returns:
            JSON响应解析后的字典
            
        Raises:
            requests.HTTPError: 如果请求失败
            json.JSONDecodeError: 如果响应不是有效的JSON
        """
        request = self._prepare_request(method, path, **kwargs)
        response = self._send_request(request)
        
        # 解析JSON响应
        try:
            return response.json()
        except json.JSONDecodeError:
            logger.error(f"无法解析JSON响应: {response.text}")
            raise
    
    def get(self, path: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """发送GET请求
        
        Args:
            path: API路径
            params: 查询参数
            **kwargs: 其他请求参数
            
        Returns:
            JSON响应解析后的字典
        """
        return self.request('GET', path, params=params, **kwargs)
    
    def post(self, path: str, data: Optional[Dict[str, Any]] = None, json_data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """发送POST请求
        
        Args:
            path: API路径
            data: 表单数据
            json_data: JSON数据
            **kwargs: 其他请求参数
            
        Returns:
            JSON响应解析后的字典
        """
        # 如果提供了json_data，则使用它
        if json_data is not None:
            kwargs['json'] = json_data
        
        return self.request('POST', path, data=data, **kwargs)
    
    def post_multipart(self, path: str, files: List[Tuple[str, Tuple[str, IO, str]]], data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """发送多部分表单上传请求
        
        Args:
            path: API路径
            files: 文件列表，格式为 [(field_name, (filename, file_obj, content_type)), ...]
            data: 表单数据
            **kwargs: 其他请求参数
            
        Returns:
            JSON响应解析后的字典
        """
        import requests
        from typing import List, Tuple, IO
        
        # 准备请求
        url = f"{self.base_url}/{path.lstrip('/')}"
        
        # 获取认证头
        headers = kwargs.get('headers', {})
        if self.auth_manager:
            auth_headers = self.auth_manager.get_auth_headers()
            headers.update(auth_headers)
        
        # 移除Content-Type，让requests自动设置合适的multipart边界
        headers.pop('Content-Type', None)
        
        # 发送请求
        logger.debug(f"发送多部分上传请求到 {url}, 文件数: {len(files)}")
        
        try:
            response = requests.post(
                url,
                files=files,
                data=data,
                headers=headers,
                timeout=self.timeout
            )
            
            # 确保所有文件都被关闭
            for _, (_, file_obj, _) in files:
                file_obj.close()
            
            # 处理响应
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            # 确保所有文件都被关闭
            for _, (_, file_obj, _) in files:
                file_obj.close()
            
            logger.error(f"多部分上传请求失败: {str(e)} - POST {url}")
            raise
        except ValueError as e:
            logger.error(f"响应解析失败: {str(e)}")
            raise
    
    def put(self, path: str, data: Optional[Dict[str, Any]] = None, json_data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """发送PUT请求
        
        Args:
            path: API路径
            data: 表单数据
            json_data: JSON数据
            **kwargs: 其他请求参数
            
        Returns:
            JSON响应解析后的字典
        """
        # 如果提供了json_data，则使用它
        if json_data is not None:
            kwargs['json'] = json_data
        
        return self.request('PUT', path, data=data, **kwargs)
    
    def delete(self, path: str, **kwargs) -> Dict[str, Any]:
        """发送DELETE请求
        
        Args:
            path: API路径
            **kwargs: 其他请求参数
            
        Returns:
            JSON响应解析后的字典
        """
        return self.request('DELETE', path, **kwargs)
    
    def upload_file(self, path: str, file_path: str, file_param: str = 'file', additional_data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """上传文件
        
        Args:
            path: API路径
            file_path: 本地文件路径
            file_param: 文件参数名
            additional_data: 其他表单数据
            **kwargs: 其他请求参数
            
        Returns:
            JSON响应解析后的字典
        """
        logger.info(f"上传文件: {file_path} 到 {path}")
        
        # 准备文件数据
        files = {file_param: open(file_path, 'rb')}
        
        try:
            # 发送请求
            result = self.request('POST', path, files=files, data=additional_data, **kwargs)
            logger.info(f"文件上传成功: {file_path}")
            return result
        finally:
            # 确保文件被关闭
            files[file_param].close()
    
    def upload_file_chunked(self, path: str, file_path: str, file_param: str = 'file', additional_data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """分块上传文件
        
        Args:
            path: API路径
            file_path: 本地文件路径
            file_param: 文件参数名
            additional_data: 其他表单数据
            **kwargs: 其他请求参数
            
        Returns:
            JSON响应解析后的字典
        """
        import os
        from pathlib import Path
        
        file_size = os.path.getsize(file_path)
        logger.info(f"开始分块上传文件: {file_path} (大小: {file_size} bytes)")
        
        # 如果文件大小小于块大小，则直接上传
        if file_size <= self.chunk_size:
            return self.upload_file(path, file_path, file_param, additional_data, **kwargs)
        
        # 创建临时文件来存储块
        temp_dir = Path(file_path).parent
        
        try:
            # 生成上传ID（实际实现中应该从服务器获取）
            upload_id = self._generate_upload_id()
            
            # 分块上传
            chunk_count = (file_size + self.chunk_size - 1) // self.chunk_size
            uploaded_chunks = []
            
            with open(file_path, 'rb') as f:
                for i in range(chunk_count):
                    # 读取块数据
                    chunk_data = f.read(self.chunk_size)
                    chunk_offset = i * self.chunk_size
                    chunk_size = len(chunk_data)
                    
                    # 记录块信息
                    chunk_info = {
                        'upload_id': upload_id,
                        'chunk_index': i,
                        'chunk_offset': chunk_offset,
                        'chunk_size': chunk_size,
                        'total_chunks': chunk_count,
                        'total_size': file_size
                    }
                    
                    # 准备上传数据
                    files = {file_param: ('chunk', chunk_data)}
                    data = additional_data.copy() if additional_data else {}
                    data.update(chunk_info)
                    
                    # 上传块
                    logger.debug(f"上传块 {i+1}/{chunk_count} ({chunk_size} bytes)")
                    chunk_response = self.request('POST', f"{path}/chunk", files=files, data=data, **kwargs)
                    
                    # 记录上传的块
                    uploaded_chunks.append(chunk_response)
                    
                    # 添加上传延迟，避免请求过于频繁
                    if i < chunk_count - 1:
                        time.sleep(0.1)
            
            # 合并块（实际实现中应该调用服务器的合并接口）
            merge_data = {
                'upload_id': upload_id,
                'total_chunks': chunk_count,
                'file_name': Path(file_path).name
            }
            
            if additional_data:
                merge_data.update(additional_data)
            
            logger.info(f"合并 {chunk_count} 个文件块")
            result = self.post(f"{path}/merge", json_data=merge_data, **kwargs)
            
            logger.info(f"文件分块上传成功: {file_path}")
            return result
            
        except Exception as e:
            logger.error(f"文件分块上传失败: {str(e)}")
            raise
    
    def download_file(self, path: str, save_path: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> str:
        """下载文件
        
        Args:
            path: API路径
            save_path: 保存路径
            params: 查询参数
            **kwargs: 其他请求参数
            
        Returns:
            保存的文件路径
        """
        import os
        from pathlib import Path
        
        # 确保保存目录存在
        save_dir = Path(save_path).parent
        save_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"下载文件: {path} 到 {save_path}")
        
        # 准备请求
        request = self._prepare_request('GET', path, params=params, **kwargs)
        prepared_request = self.session.prepare_request(request)
        
        # 发送请求并流式保存文件
        try:
            with self.session.send(prepared_request, stream=True) as response:
                response.raise_for_status()
                
                # 写入文件
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=self.chunk_size):
                        if chunk:
                            f.write(chunk)
            
            logger.info(f"文件下载成功: {save_path}")
            return save_path
            
        except Exception as e:
            # 如果下载失败，删除可能的部分文件
            if os.path.exists(save_path):
                os.remove(save_path)
            logger.error(f"文件下载失败: {str(e)}")
            raise
    
    def stream_download(self, path: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> Iterator[bytes]:
        """流式下载文件
        
        Args:
            path: API路径
            params: 查询参数
            **kwargs: 其他请求参数
            
        Yields:
            文件数据块
        """
        # 准备请求
        request = self._prepare_request('GET', path, params=params, **kwargs)
        prepared_request = self.session.prepare_request(request)
        
        # 发送请求并流式获取数据
        with self.session.send(prepared_request, stream=True) as response:
            response.raise_for_status()
            
            for chunk in response.iter_content(chunk_size=self.chunk_size):
                if chunk:
                    yield chunk
    
    def _generate_upload_id(self) -> str:
        """生成上传ID
        
        用于分块上传时标识一组块。
        
        Returns:
            上传ID
        """
        import uuid
        return str(uuid.uuid4())
    
    def close(self) -> None:
        """关闭会话"""
        if self.session:
            self.session.close()
            logger.debug("HTTP会话已关闭")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()