"""ComfyUI API客户端模块

提供与云端ComfyUI服务交互的客户端功能，封装了工作流执行、图像生成等核心API。
"""

import time
from typing import Optional, Dict, Any, List, Union
from pathlib import Path

from ..utils.logger import get_logger
from .auth import AuthManager
from .http import HttpClient

logger = get_logger(__name__)


class ComfyUIClient:
    """ComfyUI API客户端
    
    封装与云端ComfyUI服务的交互，提供工作流执行、图像生成等功能。
    """
    
    def __init__(self,
                 api_endpoint: str,
                 api_key: Optional[str] = None,
                 timeout: int = 300,
                 retry_count: int = 5,
                 retry_delay: int = 5):
        """初始化ComfyUI客户端
        
        Args:
            api_endpoint: API端点URL
            api_key: API密钥
            timeout: 请求超时时间（秒）
            retry_count: 最大重试次数
            retry_delay: 重试间隔（秒）
        """
        # 创建认证管理器
        self.auth_manager = AuthManager(api_key=api_key, api_endpoint=api_endpoint)
        
        # 创建HTTP客户端
        self.http_client = HttpClient(
            base_url=api_endpoint,
            auth_manager=self.auth_manager,
            timeout=timeout,
            retry_count=retry_count,
            retry_delay=retry_delay
        )
        
        logger.info(f"ComfyUI客户端已初始化: {api_endpoint}")
    
    def execute_workflow(self, workflow_data: Dict[str, Any], wait_for_completion: bool = True, poll_interval: int = 5) -> Dict[str, Any]:
        """执行工作流
        
        Args:
            workflow_data: 工作流数据
            wait_for_completion: 是否等待工作流完成
            poll_interval: 状态轮询间隔（秒）
            
        Returns:
            工作流执行结果
        """
        logger.info("执行ComfyUI工作流")
        
        # 发送工作流执行请求
        response = self.http_client.post('/workflows/execute', json_data=workflow_data)
        
        # 获取任务ID
        task_id = response.get('task_id')
        if not task_id:
            raise ValueError("未获取到任务ID")
        
        logger.info(f"工作流任务已创建: {task_id}")
        
        # 如果不需要等待完成，则直接返回任务信息
        if not wait_for_completion:
            return response
        
        # 等待工作流完成
        return self.wait_for_task_completion(task_id, poll_interval)
    
    def wait_for_task_completion(self, task_id: str, poll_interval: int = 5) -> Dict[str, Any]:
        """等待任务完成
        
        Args:
            task_id: 任务ID
            poll_interval: 状态轮询间隔（秒）
            
        Returns:
            任务完成后的结果
        """
        logger.info(f"等待任务完成: {task_id}")
        
        while True:
            # 获取任务状态
            task_status = self.get_task_status(task_id)
            status = task_status.get('status')
            
            logger.debug(f"任务状态: {status} - {task_id}")
            
            # 检查任务是否完成
            if status == 'completed':
                logger.info(f"任务已完成: {task_id}")
                return task_status
            elif status == 'failed':
                error_message = task_status.get('error', '未知错误')
                logger.error(f"任务执行失败: {task_id} - {error_message}")
                raise RuntimeError(f"工作流执行失败: {error_message}")
            elif status == 'canceled':
                logger.warning(f"任务已取消: {task_id}")
                raise RuntimeError("工作流执行已被取消")
            
            # 等待指定时间后再次查询
            time.sleep(poll_interval)
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态信息
        """
        return self.http_client.get(f'/tasks/{task_id}')
    
    def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            取消操作的结果
        """
        logger.info(f"取消任务: {task_id}")
        return self.http_client.post(f'/tasks/{task_id}/cancel')
    
    def generate_image(self, prompt: str, negative_prompt: str = "", params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """生成图像
        
        Args:
            prompt: 正面提示词
            negative_prompt: 负面提示词
            params: 其他生成参数
            
        Returns:
            图像生成结果
        """
        logger.info(f"生成图像: {prompt[:50]}...")
        
    def upload_video_frames(self, frames_dir: str, task_id: str) -> Dict[str, Any]:
        """上传视频帧到任务
        
        Args:
            frames_dir: 视频帧目录
            task_id: 任务ID
            
        Returns:
            上传结果
        """
        logger.info(f"上传视频帧到任务 {task_id}")
        
        # 构建上传URL
        upload_url = f"/tasks/{task_id}/upload_frames"
        
        # 准备上传数据
        files = []
        import os
        for filename in os.listdir(frames_dir):
            if filename.endswith(('.png', '.jpg', '.jpeg')):
                file_path = os.path.join(frames_dir, filename)
                files.append(('frames', (filename, open(file_path, 'rb'), 'image/png')))
        
        # 上传文件
        try:
            response = self.http_client.post_multipart(upload_url, files=files)
            logger.info(f"成功上传 {len(files)} 个视频帧")
            return response
        except Exception as e:
            logger.error(f"上传视频帧失败: {str(e)}")
            raise
    
    def execute_replacement_task(self, task_config: Dict[str, Any]) -> Dict[str, Any]:
        """执行替换任务
        
        Args:
            task_config: 任务配置，包含替换类型和参数
            
        Returns:
            任务执行结果
        """
        logger.info("执行替换任务")
        
        # 构建API请求数据
        request_data = {
            'task_type': task_config.get('task_type', 'video_replication'),
            'params': task_config.get('params', {})
        }
        
        # 发送请求
        response = self.http_client.post('/tasks/replacement/execute', json_data=request_data)
        logger.info(f"替换任务已创建: {response.get('task_id')}")
        return response
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        """列出可用工作流
        
        Returns:
            工作流列表
        """
        logger.info("获取工作流列表")
        try:
            response = self.http_client.get('/workflows')
            return response.get('workflows', [])
        except Exception as e:
            logger.error(f"获取工作流列表失败: {str(e)}")
            return []
    
    def test_connection(self) -> bool:
        """测试与ComfyUI API的连接
        
        Returns:
            连接是否成功
        """
        try:
            response = self.http_client.get('/health')
            return response.get('status') == 'ok'
        except Exception as e:
            logger.warning(f"连接测试失败: {str(e)}")
            return False
    
    def close(self):
        """关闭客户端连接"""
        # 可以在这里释放资源
        logger.info("ComfyUI客户端已关闭")
        
        # 构建请求数据
        data = {
            'prompt': prompt,
            'negative_prompt': negative_prompt,
            'params': params or {}
        }
        
        # 发送生成请求
        return self.http_client.post('/images/generate', json_data=data)
    
    def process_image(self, image_path: str, process_type: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """处理图像
        
        Args:
            image_path: 图像文件路径
            process_type: 处理类型
            params: 处理参数
            
        Returns:
            图像处理结果
        """
        logger.info(f"处理图像: {image_path}, 类型: {process_type}")
        
        # 准备额外数据
        additional_data = params.copy() if params else {}
        additional_data['process_type'] = process_type
        
        # 上传并处理图像
        return self.http_client.upload_file('/images/process', image_path, 'image', additional_data)
    
    def upload_image(self, image_path: str, category: str = 'input') -> Dict[str, Any]:
        """上传图像
        
        Args:
            image_path: 图像文件路径
            category: 图像类别
            
        Returns:
            上传结果
        """
        logger.info(f"上传图像: {image_path}, 类别: {category}")
        
        # 准备上传数据
        data = {'category': category}
        
        # 执行上传
        return self.http_client.upload_file('/images/upload', image_path, 'image', data)
    
    def download_image(self, image_id: str, save_path: str) -> str:
        """下载图像
        
        Args:
            image_id: 图像ID
            save_path: 保存路径
            
        Returns:
            保存的文件路径
        """
        logger.info(f"下载图像: {image_id} 到 {save_path}")
        
        # 执行下载
        return self.http_client.download_file(f'/images/{image_id}/download', save_path)
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        """列出可用的工作流
        
        Returns:
            工作流列表
        """
        logger.info("获取工作流列表")
        response = self.http_client.get('/workflows')
        return response.get('workflows', [])
    
    def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """获取工作流详情
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            工作流详情
        """
        logger.info(f"获取工作流详情: {workflow_id}")
        return self.http_client.get(f'/workflows/{workflow_id}')
    
    def create_workflow(self, name: str, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建新工作流
        
        Args:
            name: 工作流名称
            workflow_data: 工作流数据
            
        Returns:
            创建的工作流信息
        """
        logger.info(f"创建工作流: {name}")
        data = {
            'name': name,
            'workflow_data': workflow_data
        }
        return self.http_client.post('/workflows', json_data=data)
    
    def update_workflow(self, workflow_id: str, name: Optional[str] = None, workflow_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """更新工作流
        
        Args:
            workflow_id: 工作流ID
            name: 新的工作流名称（可选）
            workflow_data: 新的工作流数据（可选）
            
        Returns:
            更新后的工作流信息
        """
        logger.info(f"更新工作流: {workflow_id}")
        data = {}
        if name is not None:
            data['name'] = name
        if workflow_data is not None:
            data['workflow_data'] = workflow_data
        return self.http_client.put(f'/workflows/{workflow_id}', json_data=data)
    
    def delete_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """删除工作流
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            删除操作的结果
        """
        logger.info(f"删除工作流: {workflow_id}")
        return self.http_client.delete(f'/workflows/{workflow_id}')
    
    def get_model_list(self, model_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取可用模型列表
        
        Args:
            model_type: 模型类型（可选）
            
        Returns:
            模型列表
        """
        logger.info(f"获取模型列表，类型: {model_type or 'all'}")
        params = {'type': model_type} if model_type else {}
        response = self.http_client.get('/models', params=params)
        return response.get('models', [])
    
    def get_usage_statistics(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """获取使用统计信息
        
        Args:
            start_date: 开始日期（YYYY-MM-DD格式）
            end_date: 结束日期（YYYY-MM-DD格式）
            
        Returns:
            使用统计信息
        """
        logger.info(f"获取使用统计: {start_date} 到 {end_date}")
        params = {}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        return self.http_client.get('/usage/statistics', params=params)
    
    def get_api_status(self) -> Dict[str, Any]:
        """获取API服务状态
        
        Returns:
            API服务状态信息
        """
        logger.info("检查API服务状态")
        return self.http_client.get('/status')
    
    def test_connection(self) -> bool:
        """测试连接
        
        Returns:
            连接成功返回True，否则返回False
        """
        try:
            status = self.get_api_status()
            is_connected = status.get('status') == 'ok'
            
            if is_connected:
                logger.info("成功连接到ComfyUI API服务")
            else:
                logger.warning(f"API服务状态异常: {status}")
            
            return is_connected
        
        except Exception as e:
            logger.error(f"连接测试失败: {str(e)}")
            return False
    
    def upload_video_frames(self, frames_dir: str, task_id: str) -> Dict[str, Any]:
        """上传视频帧
        
        Args:
            frames_dir: 包含视频帧的目录
            task_id: 任务ID
            
        Returns:
            上传结果
        """
        logger.info(f"上传视频帧，目录: {frames_dir}, 任务: {task_id}")
        
        # 获取所有帧文件
        frame_files = sorted([f for f in Path(frames_dir).iterdir() if f.is_file()])
        
        if not frame_files:
            raise ValueError(f"目录中没有找到视频帧: {frames_dir}")
        
        logger.info(f"找到 {len(frame_files)} 个视频帧")
        
        # 批量上传帧
        upload_results = []
        for i, frame_file in enumerate(frame_files):
            logger.debug(f"上传帧 {i+1}/{len(frame_files)}: {frame_file.name}")
            
            # 准备上传数据
            data = {
                'task_id': task_id,
                'frame_index': i,
                'total_frames': len(frame_files)
            }
            
            # 上传帧
            result = self.http_client.upload_file('/videos/frames/upload', str(frame_file), 'frame', data)
            upload_results.append(result)
            
            # 避免请求过于频繁
            if i < len(frame_files) - 1:
                time.sleep(0.1)
        
        return {
            'task_id': task_id,
            'uploaded_frames': len(upload_results),
            'total_frames': len(frame_files),
            'results': upload_results
        }
    
    def download_video_result(self, task_id: str, save_path: str) -> str:
        """下载视频处理结果
        
        Args:
            task_id: 任务ID
            save_path: 保存路径
            
        Returns:
            保存的文件路径
        """
        logger.info(f"下载视频结果: {task_id} 到 {save_path}")
        
        # 确保保存目录存在
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        
        # 执行下载
        return self.http_client.download_file(f'/videos/results/{task_id}', save_path)
    
    def close(self) -> None:
        """关闭客户端连接"""
        if self.http_client:
            self.http_client.close()
            logger.info("ComfyUI客户端已关闭")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()