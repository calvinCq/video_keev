"""工作流管理器实现

负责协调整个视频复刻流程，包括任务执行、状态管理和进度跟踪。
"""

import os
import time
import uuid
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

from ..utils.logger import get_logger
from ..utils.file_utils import ensure_directory, remove_directory
from ..config.manager import ConfigManager
from ..api.client import ComfyUIClient
from ..video.processor import VideoProcessor
from .replacement_processor import replacement_processor

logger = get_logger(__name__)


class WorkflowManager:
    """工作流管理器类
    
    负责协调整个视频复刻流程，管理工作流状态和执行进度。
    """
    
    # 工作流状态常量
    STATUS_IDLE = 'idle'
    STATUS_PREPARING = 'preparing'
    STATUS_EXTRACTING_FRAMES = 'extracting_frames'
    STATUS_PREPROCESSING_FRAMES = 'preprocessing_frames'
    STATUS_UPLOADING_FRAMES = 'uploading_frames'
    STATUS_EXECUTING_WORKFLOW = 'executing_workflow'
    STATUS_DOWNLOADING_RESULTS = 'downloading_results'
    STATUS_COMPOSING_VIDEO = 'composing_video'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    STATUS_CANCELED = 'canceled'
    
    def __init__(self, config: Optional[ConfigManager] = None):
        """初始化工作流管理器
        
        Args:
            config: 配置管理器实例，如果为None则使用默认配置
        """
        self.config = config or ConfigManager()
        
        # 初始化组件
        self.video_processor = VideoProcessor(
            temp_dir=self.config.get('video.temp_dir'),
            output_dir=self.config.get('video.output_dir')
        )
        
        # 初始化替换处理器（使用全局实例）
        self.replacement_processor = replacement_processor
        
        self.comfyui_client = ComfyUIClient(
            api_endpoint=self.config.get('comfyui.api_endpoint'),
            api_key=os.getenv('COMFYUI_API_KEY'),
            timeout=self.config.get('comfyui.timeout'),
            retry_count=self.config.get('comfyui.retry_count'),
            retry_delay=self.config.get('comfyui.retry_delay')
        )
        
        # 工作流状态
        self.workflow_id: Optional[str] = None
        self.status = self.STATUS_IDLE
        self.progress = 0.0
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        
        # 工作流数据
        self.working_dir: Optional[str] = None
        self.input_video_path: Optional[str] = None
        self.output_video_path: Optional[str] = None
        self.frame_paths: List[str] = []
        self.processed_frame_paths: List[str] = []
        self.task_id: Optional[str] = None
        
        logger.info("工作流管理器已初始化")
    
    def start_workflow(self, input_video: str, workflow_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """启动视频复刻工作流
        
        Args:
            input_video: 输入视频路径
            workflow_config: 工作流配置参数
            
        Returns:
            工作流信息
        """
        try:
            # 验证输入
            if not os.path.exists(input_video):
                raise FileNotFoundError(f"输入视频不存在: {input_video}")
            
            # 重置状态
            self._reset_state()
            
            # 初始化工作流
            self.workflow_id = str(uuid.uuid4())
            self.input_video_path = input_video
            self.status = self.STATUS_PREPARING
            self.start_time = time.time()
            
            # 创建工作目录
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.working_dir = os.path.join(self.config.get('video.temp_dir'), f"workflow_{timestamp}_{self.workflow_id[:8]}")
            ensure_directory(self.working_dir)
            
            # 初始化输出路径
            video_name = os.path.splitext(os.path.basename(input_video))[0]
            output_video_name = f"{video_name}_replicated.mp4"
            self.output_video_path = os.path.join(self.config.get('video.output_dir'), output_video_name)
            
            # 记录工作流开始
            logger.info(f"开始工作流: {self.workflow_id} - 输入视频: {input_video}")
            
            # 异步执行工作流（实际实现中可能需要使用线程或任务队列）
            self._execute_workflow_steps(workflow_config or {})
            
            return {
                'workflow_id': self.workflow_id,
                'status': self.status,
                'input_video': self.input_video_path,
                'output_video': self.output_video_path,
                'started_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self._set_failed_state(str(e))
            raise
    
    def _execute_workflow_steps(self, workflow_config: Dict[str, Any]) -> None:
        """执行工作流步骤
        
        Args:
            workflow_config: 工作流配置参数
        """
        try:
            # 获取视频信息
            self._update_status(self.STATUS_PREPARING)
            video_info = self.video_processor.get_video_info(self.input_video_path)
            logger.info(f"视频信息: {video_info}")
            
            # 检查是否启用了替换功能
            has_replacement = False
            if 'replacement' in workflow_config:
                replacement_config = workflow_config['replacement']
                has_replacement = (replacement_config.get('person', {}).get('enabled', False) or
                                   replacement_config.get('background', {}).get('enabled', False) or
                                   replacement_config.get('product', {}).get('enabled', False))
            
            # 1. 提取视频帧
            self._update_status(self.STATUS_EXTRACTING_FRAMES)
            frames_dir = os.path.join(self.working_dir, 'frames')
            frame_rate = workflow_config.get('frame_rate', video_info['fps'])
            max_frames = workflow_config.get('max_frames')
            
            self.frame_paths = self.video_processor.extract_frames(
                self.input_video_path,
                frames_dir,
                frame_rate,
                max_frames
            )
            self._update_progress(20.0)
            
            # 2. 预处理帧
            self._update_status(self.STATUS_PREPROCESSING_FRAMES)
            processed_dir = os.path.join(self.working_dir, 'processed_frames')
            preprocess_config = workflow_config.get('preprocess', {})
            
            # 如果启用了替换功能，调整预处理参数
            if has_replacement:
                # 为替换任务优化预处理参数
                preprocess_config['enhance_features'] = True
                preprocess_config['preserve_details'] = True
                logger.info("为替换任务优化预处理参数")
            
            # 执行帧预处理
            self.processed_frame_paths = self.video_processor.preprocess_frames(
                self.frame_paths,
                processed_dir,
                **preprocess_config
            )
            self._update_progress(40.0)
            
            # 3. 本地替换预处理（可选）
            if has_replacement:
                self._update_status("local_replacement_preprocessing")
                logger.info("执行本地替换预处理")
                
                # 创建替换处理目录
                replaced_dir = os.path.join(self.working_dir, 'replaced_frames')
                
                # 使用替换处理器进行本地预处理
                local_replaced_paths = self.replacement_processor.process_frames_batch(
                    self.processed_frame_paths,
                    workflow_config['replacement'],
                    replaced_dir
                )
                
                # 更新处理后的帧路径
                self.processed_frame_paths = local_replaced_paths
                logger.info("本地替换预处理完成")
            
            # 继续原有流程
            
            # 3. 测试ComfyUI连接
            if not self.comfyui_client.test_connection():
                raise RuntimeError("无法连接到ComfyUI API服务")
            
            # 4. 创建任务并上传帧
            self._update_status(self.STATUS_UPLOADING_FRAMES)
            
            # 准备工作流数据
            workflow_data = self._prepare_workflow_data(workflow_config, video_info)
            
            # 创建任务
            if has_replacement:
                # 执行替换任务
                logger.info("执行替换任务")
                task_response = self.comfyui_client.execute_replacement_task(workflow_data)
            else:
                # 执行普通工作流
                task_response = self.comfyui_client.execute_workflow(
                    workflow_data,
                    wait_for_completion=False
                )
            
            self.task_id = task_response.get('task_id')
            if not self.task_id:
                raise ValueError("未获取到任务ID")
            
            # 上传帧
            upload_result = self.comfyui_client.upload_video_frames(
                processed_dir,
                self.task_id
            )
            self._update_progress(60.0)
            
            # 5. 等待工作流执行完成
            self._update_status(self.STATUS_EXECUTING_WORKFLOW)
            logger.info(f"等待云端工作流执行完成: {self.task_id}")
            
            task_result = self.comfyui_client.wait_for_task_completion(
                self.task_id,
                poll_interval=workflow_config.get('poll_interval', 5)
            )
            self._update_progress(80.0)
            
            # 6. 下载处理结果
            self._update_status(self.STATUS_DOWNLOADING_RESULTS)
            
            # 创建结果目录
            results_dir = os.path.join(self.working_dir, 'results')
            ensure_directory(results_dir)
            
            # 下载处理后的帧
            result_frame_paths = []
            
            # 实际实现中，这里应该从task_result中获取处理后的帧信息并下载
            # 检查是否有替换结果
            if has_replacement and 'replaced_frames' in task_result:
                # 这里应该从云端下载替换后的帧
                # 简化实现，仍然使用处理后的帧
                logger.info(f"获取到替换结果，共 {len(task_result['replaced_frames'])} 帧")
                result_frame_paths = self.processed_frame_paths
            else:
                result_frame_paths = self.processed_frame_paths
            
            self._update_progress(90.0)
            
            # 7. 合成视频
            self._update_status(self.STATUS_COMPOSING_VIDEO)
            
            # 确保输出目录存在
            ensure_directory(os.path.dirname(self.output_video_path))
            
            # 合成视频
            self.video_processor.frames_to_video(
                result_frame_paths,
                self.output_video_path,
                fps=frame_rate
            )
            self._update_progress(100.0)
            
            # 标记完成
            self._update_status(self.STATUS_COMPLETED)
            self.end_time = time.time()
            
            logger.info(f"工作流完成: {self.workflow_id} - 输出视频: {self.output_video_path}")
            
        except Exception as e:
            self._set_failed_state(str(e))
            raise
    
    def _prepare_workflow_data(self, workflow_config: Dict[str, Any], video_info: Dict[str, Any]) -> Dict[str, Any]:
        """准备工作流数据
        
        Args:
            workflow_config: 工作流配置
            video_info: 视频信息
            
        Returns:
            工作流数据
        """
        # 获取默认工作流配置
        default_workflow = self.config.get('workflows.default', {})
        
        # 构建工作流数据
        workflow_data = {
            'id': workflow_config.get('workflow_id', default_workflow.get('id', 'default_video_replication')),
            'params': {
                'model_id': workflow_config.get('model_id', default_workflow.get('params', {}).get('model_id', 'realistic_video_v1')),
                'quality_level': workflow_config.get('quality_level', default_workflow.get('params', {}).get('quality_level', 'high')),
                'video_resolution': {
                    'width': video_info['width'],
                    'height': video_info['height']
                },
                'frame_count': len(self.frame_paths),
                'fps': workflow_config.get('frame_rate', video_info['fps'])
            }
        }
        
        # 添加其他自定义参数
        if 'custom_params' in workflow_config:
            workflow_data['params'].update(workflow_config['custom_params'])
        
        # 添加替换相关参数
        if 'replacement' in workflow_config:
            replacement_config = workflow_config['replacement']
            
            # 添加任务替换参数
            workflow_data['params']['task_type'] = 'video_replication'
            
            # 处理人物替换
            if replacement_config.get('person', {}).get('enabled', False):
                person_config = replacement_config['person']
                workflow_data['params']['person_replacement'] = {
                    'enabled': True,
                    'target_description': person_config.get('target_description', ''),
                    'replacement_image': person_config.get('replacement_image', ''),
                    'preserve_pose': person_config.get('preserve_pose', True),
                    'confidence_threshold': person_config.get('confidence_threshold', 0.7)
                }
            
            # 处理背景替换
            if replacement_config.get('background', {}).get('enabled', False):
                background_config = replacement_config['background']
                workflow_data['params']['background_replacement'] = {
                    'enabled': True,
                    'prompt': background_config.get('prompt', ''),
                    'negative_prompt': background_config.get('negative_prompt', ''),
                    'preserve_foreground': background_config.get('preserve_foreground', True),
                    'blur_strength': background_config.get('blur_strength', 0.3)
                }
            
            # 处理商品替换
            if replacement_config.get('product', {}).get('enabled', False):
                product_config = replacement_config['product']
                workflow_data['params']['product_replacement'] = {
                    'enabled': True,
                    'target_description': product_config.get('target_description', ''),
                    'replacement_image': product_config.get('replacement_image', ''),
                    'product_mask_prompt': product_config.get('product_mask_prompt', ''),
                    'preserve_lighting': product_config.get('preserve_lighting', True),
                    'shadow_intensity': product_config.get('shadow_intensity', 0.5)
                }
        
        return workflow_data
    
    def _update_status(self, status: str) -> None:
        """更新工作流状态
        
        Args:
            status: 新的状态
        """
        self.status = status
        logger.info(f"工作流 {self.workflow_id} 状态更新为: {status}")
    
    def _update_progress(self, progress: float) -> None:
        """更新工作流进度
        
        Args:
            progress: 进度百分比（0-100）
        """
        self.progress = min(100.0, max(0.0, progress))
        logger.debug(f"工作流 {self.workflow_id} 进度: {self.progress:.1f}%")
    
    def _set_failed_state(self, error_message: str) -> None:
        """设置工作流为失败状态
        
        Args:
            error_message: 错误信息
        """
        self.status = self.STATUS_FAILED
        self.end_time = time.time()
        logger.error(f"工作流 {self.workflow_id} 失败: {error_message}")
    
    def _reset_state(self) -> None:
        """重置工作流状态"""
        self.workflow_id = None
        self.status = self.STATUS_IDLE
        self.progress = 0.0
        self.start_time = None
        self.end_time = None
        self.working_dir = None
        self.input_video_path = None
        self.output_video_path = None
        self.frame_paths = []
        self.processed_frame_paths = []
        self.task_id = None
    
    def get_status(self) -> Dict[str, Any]:
        """获取工作流状态
        
        Returns:
            工作流状态信息
        """
        status_info = {
            'workflow_id': self.workflow_id,
            'status': self.status,
            'progress': self.progress,
            'input_video': self.input_video_path,
            'output_video': self.output_video_path,
            'task_id': self.task_id
        }
        
        # 添加时间信息
        if self.start_time:
            status_info['started_at'] = datetime.fromtimestamp(self.start_time).isoformat()
            
            if self.end_time:
                status_info['ended_at'] = datetime.fromtimestamp(self.end_time).isoformat()
                status_info['duration'] = self.end_time - self.start_time
            else:
                status_info['duration'] = time.time() - self.start_time
        
        return status_info
    
    def cancel_workflow(self) -> Dict[str, Any]:
        """取消工作流
        
        Returns:
            取消结果
        """
        if self.status in [self.STATUS_COMPLETED, self.STATUS_FAILED, self.STATUS_CANCELED]:
            return {'success': False, 'message': '工作流已结束，无法取消'}
        
        try:
            # 更新状态
            self.status = self.STATUS_CANCELED
            self.end_time = time.time()
            
            # 如果有任务ID，则尝试取消云端任务
            if self.task_id:
                try:
                    cancel_result = self.comfyui_client.cancel_task(self.task_id)
                    logger.info(f"云端任务已取消: {self.task_id}")
                except Exception as e:
                    logger.warning(f"取消云端任务失败: {str(e)}")
            
            logger.info(f"工作流已取消: {self.workflow_id}")
            
            return {
                'success': True,
                'message': '工作流已取消',
                'workflow_id': self.workflow_id
            }
            
        except Exception as e:
            logger.error(f"取消工作流失败: {str(e)}")
            return {
                'success': False,
                'message': f'取消失败: {str(e)}'
            }
    
    def cleanup(self, keep_results: bool = True) -> None:
        """清理工作流资源
        
        Args:
            keep_results: 是否保留结果文件
        """
        # 关闭客户端连接
        self.comfyui_client.close()
        
        # 清理临时目录
        if self.working_dir and os.path.exists(self.working_dir):
            logger.info(f"清理临时工作目录: {self.working_dir}")
            remove_directory(self.working_dir)
        
        if not keep_results and self.output_video_path and os.path.exists(self.output_video_path):
            logger.info(f"清理结果文件: {self.output_video_path}")
            os.remove(self.output_video_path)
        
        logger.info("工作流资源清理完成")
    
    def list_available_workflows(self) -> List[Dict[str, Any]]:
        """列出可用的工作流
        
        Returns:
            工作流列表
        """
        try:
            # 获取云端工作流列表
            cloud_workflows = self.comfyui_client.list_workflows()
            
            # 获取本地配置的工作流
            local_workflows = self.config.get('workflows', {})
            
            # 合并并返回
            available_workflows = []
            
            # 添加本地配置的工作流
            for name, workflow in local_workflows.items():
                available_workflows.append({
                    'id': workflow.get('id', name),
                    'name': name,
                    'source': 'local',
                    'params': workflow.get('params', {})
                })
            
            # 添加云端工作流
            for workflow in cloud_workflows:
                # 避免重复
                if not any(w['id'] == workflow['id'] for w in available_workflows):
                    available_workflows.append({
                        'id': workflow['id'],
                        'name': workflow.get('name', workflow['id']),
                        'source': 'cloud',
                        'params': workflow.get('params', {})
                    })
            
            return available_workflows
            
        except Exception as e:
            logger.error(f"获取工作流列表失败: {str(e)}")
            return []