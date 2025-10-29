"""视频处理器实现

负责视频帧提取、预处理和后处理（帧合成）等功能。
"""

import os
import cv2
import time
import numpy as np
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..utils.logger import get_logger
from ..utils.file_utils import ensure_directory, safe_copy

logger = get_logger(__name__)


class VideoProcessor:
    """视频处理器类
    
    提供视频帧提取、预处理和后处理功能。
    """
    
    def __init__(self, temp_dir: str = './temp', output_dir: str = './outputs', max_workers: int = 4):
        """初始化视频处理器
        
        Args:
            temp_dir: 临时文件目录
            output_dir: 输出文件目录
            max_workers: 并行处理的最大工作线程数
        """
        self.temp_dir = temp_dir
        self.output_dir = output_dir
        self.max_workers = max_workers
        
        # 确保目录存在
        ensure_directory(temp_dir)
        ensure_directory(output_dir)
        
        logger.info(f"视频处理器已初始化 - 临时目录: {temp_dir}, 输出目录: {output_dir}")
    
    def extract_frames(self, video_path: str, output_dir: Optional[str] = None, frame_rate: Optional[int] = None, max_frames: Optional[int] = None) -> List[str]:
        """从视频中提取帧
        
        Args:
            video_path: 视频文件路径
            output_dir: 帧保存目录，如果为None则使用临时目录
            frame_rate: 提取帧率，如果为None则使用视频原始帧率
            max_frames: 最大提取帧数
            
        Returns:
            提取的帧文件路径列表
        """
        start_time = time.time()
        
        # 验证视频文件
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        # 设置输出目录
        if output_dir is None:
            # 创建基于时间戳的临时目录
            timestamp = int(time.time())
            output_dir = os.path.join(self.temp_dir, f"frames_{timestamp}")
        
        ensure_directory(output_dir)
        
        logger.info(f"开始提取视频帧 - 输入: {video_path}, 输出: {output_dir}")
        
        # 打开视频
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {video_path}")
        
        # 获取视频信息
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / video_fps if video_fps > 0 else 0
        
        logger.info(f"视频信息 - 帧率: {video_fps:.2f}, 总帧数: {total_frames}, 时长: {duration:.2f}秒")
        
        # 确定提取参数
        extract_interval = 1  # 默认每一帧都提取
        if frame_rate is not None and frame_rate < video_fps:
            extract_interval = int(video_fps / frame_rate)
        
        # 确定要提取的最大帧数
        if max_frames is not None and max_frames < total_frames:
            total_frames_to_extract = min(max_frames, total_frames)
        else:
            total_frames_to_extract = total_frames
        
        logger.info(f"提取配置 - 提取间隔: {extract_interval}, 预计提取帧数: {total_frames_to_extract}")
        
        # 提取帧
        frame_paths = []
        frame_count = 0
        extracted_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 按照提取间隔提取帧
            if frame_count % extract_interval == 0:
                # 保存帧
                frame_filename = f"frame_{extracted_count:06d}.png"
                frame_path = os.path.join(output_dir, frame_filename)
                
                # 使用无损压缩保存帧
                cv2.imwrite(frame_path, frame, [cv2.IMWRITE_PNG_COMPRESSION, 0])
                frame_paths.append(frame_path)
                extracted_count += 1
                
                # 检查是否达到最大提取帧数
                if max_frames is not None and extracted_count >= max_frames:
                    break
            
            frame_count += 1
            
            # 记录进度
            if frame_count % 100 == 0 or frame_count == total_frames:
                progress = (frame_count / total_frames) * 100
                logger.debug(f"帧提取进度: {frame_count}/{total_frames} ({progress:.1f}%)")
        
        # 释放资源
        cap.release()
        
        # 计算处理时间
        elapsed_time = time.time() - start_time
        logger.info(f"视频帧提取完成 - 共提取 {extracted_count} 帧, 耗时: {elapsed_time:.2f} 秒")
        
        return frame_paths
    
    def preprocess_frames(self, frame_paths: List[str], output_dir: Optional[str] = None, **kwargs) -> List[str]:
        """预处理视频帧
        
        Args:
            frame_paths: 帧文件路径列表
            output_dir: 预处理后帧保存目录
            **kwargs: 预处理参数
                - resize: 调整大小 (width, height)
                - normalize: 是否归一化
                - grayscale: 是否转换为灰度图
                - enhance_features: 是否增强特征（用于替换任务）
                - preserve_details: 是否保留细节（用于替换任务）
            
        Returns:
            预处理后的帧文件路径列表
        """
        start_time = time.time()
        
        # 设置输出目录
        if output_dir is None:
            # 创建基于时间戳的临时目录
            timestamp = int(time.time())
            output_dir = os.path.join(self.temp_dir, f"processed_frames_{timestamp}")
        
        ensure_directory(output_dir)
        
        logger.info(f"开始预处理视频帧 - 总帧数: {len(frame_paths)}, 输出目录: {output_dir}")
        
        # 获取预处理参数
        resize = kwargs.get('resize')
        normalize = kwargs.get('normalize', False)
        grayscale = kwargs.get('grayscale', False)
        enhance_features = kwargs.get('enhance_features', False)
        preserve_details = kwargs.get('preserve_details', False)
        
        # 预处理结果
        processed_paths = []
        
        # 使用线程池并行处理帧
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交任务
            future_to_frame = {
                executor.submit(self._preprocess_single_frame, frame_path, output_dir, resize, normalize, grayscale, enhance_features, preserve_details): frame_path 
                for frame_path in frame_paths
            }
            
            # 收集结果
            for i, future in enumerate(as_completed(future_to_frame)):
                try:
                    processed_path = future.result()
                    processed_paths.append(processed_path)
                    
                    # 记录进度
                    if (i + 1) % 20 == 0 or (i + 1) == len(frame_paths):
                        progress = ((i + 1) / len(frame_paths)) * 100
                        logger.debug(f"帧预处理进度: {i + 1}/{len(frame_paths)} ({progress:.1f}%)")
                        
                except Exception as e:
                    frame_path = future_to_frame[future]
                    logger.error(f"预处理帧失败: {frame_path}, 错误: {str(e)}")
        
        # 计算处理时间
        elapsed_time = time.time() - start_time
        logger.info(f"视频帧预处理完成 - 成功处理 {len(processed_paths)} 帧, 耗时: {elapsed_time:.2f} 秒")
        
        return processed_paths
    
    def _preprocess_single_frame(self, frame_path: str, output_dir: str, resize: Optional[Tuple[int, int]] = None, normalize: bool = False, grayscale: bool = False, enhance_features: bool = False, preserve_details: bool = False) -> str:
        """预处理单个帧
        
        Args:
            frame_path: 帧文件路径
            output_dir: 输出目录
            resize: 调整大小 (width, height)
            normalize: 是否归一化
            grayscale: 是否转换为灰度图
            enhance_features: 是否增强特征
            preserve_details: 是否保留细节
            
        Returns:
            预处理后的帧文件路径
        """
        # 读取帧
        frame = cv2.imread(frame_path)
        
        # 处理帧
        if grayscale:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        if resize:
            if preserve_details:
                # 使用高质量的插值方法保留细节
                frame = cv2.resize(frame, resize, interpolation=cv2.INTER_LANCZOS4)
            else:
                frame = cv2.resize(frame, resize)
        
        # 增强特征（用于更好的对象检测和分割）
        if enhance_features and not grayscale:
            # 转换到YUV色彩空间进行亮度调整
            yuv = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV)
            y, u, v = cv2.split(yuv)
            
            # 应用自适应直方图均衡化增强对比度
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            cl1 = clahe.apply(y)
            
            # 合并通道
            enhanced_yuv = cv2.merge((cl1, u, v))
            frame = cv2.cvtColor(enhanced_yuv, cv2.COLOR_YUV2BGR)
            
            # 轻微锐化以增强边缘特征
            kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
            frame = cv2.filter2D(frame, -1, kernel)
        
        if normalize and frame.dtype == 'uint8':
            frame = frame.astype('float32') / 255.0
        
        # 保存处理后的帧
        frame_filename = os.path.basename(frame_path)
        output_path = os.path.join(output_dir, frame_filename)
        
        # 根据是否归一化选择保存方式
        if normalize and frame.dtype == 'float32':
            # 如果是归一化的浮点数组，转换回uint8
            frame = (frame * 255).astype('uint8')
        
        # 设置保存参数
        if preserve_details:
            # 使用高质量压缩保留细节
            if frame_path.endswith('.jpg'):
                cv2.imwrite(output_path, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
            else:
                cv2.imwrite(output_path, frame, [int(cv2.IMWRITE_PNG_COMPRESSION), 1])
        else:
            cv2.imwrite(output_path, frame, [cv2.IMWRITE_PNG_COMPRESSION, 3])
        
        return output_path
    
    def frames_to_video(self, frame_paths: List[str], output_path: str, fps: float = 30.0, codec: str = 'mp4v') -> str:
        """将帧合成视频
        
        Args:
            frame_paths: 帧文件路径列表
            output_path: 输出视频路径
            fps: 视频帧率
            codec: 视频编码器
            
        Returns:
            合成的视频文件路径
        """
        start_time = time.time()
        
        if not frame_paths:
            raise ValueError("帧列表为空")
        
        # 确保输出目录存在
        ensure_directory(os.path.dirname(output_path))
        
        logger.info(f"开始合成视频 - 帧数: {len(frame_paths)}, 帧率: {fps}, 输出: {output_path}")
        
        # 读取第一个帧获取尺寸
        first_frame = cv2.imread(frame_paths[0])
        if first_frame is None:
            raise ValueError(f"无法读取第一个帧: {frame_paths[0]}")
        
        height, width = first_frame.shape[:2]
        
        # 创建视频写入器
        fourcc = cv2.VideoWriter_fourcc(*codec)
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # 写入帧
        written_frames = 0
        
        for i, frame_path in enumerate(frame_paths):
            # 读取帧
            frame = cv2.imread(frame_path)
            if frame is None:
                logger.warning(f"跳过无效帧: {frame_path}")
                continue
            
            # 调整帧大小以匹配视频尺寸
            if frame.shape[0] != height or frame.shape[1] != width:
                frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_LANCZOS4)
            
            # 写入帧
            out.write(frame)
            written_frames += 1
            
            # 记录进度
            if (i + 1) % 100 == 0 or (i + 1) == len(frame_paths):
                progress = ((i + 1) / len(frame_paths)) * 100
                logger.debug(f"视频合成进度: {i + 1}/{len(frame_paths)} ({progress:.1f}%)")
        
        # 释放资源
        out.release()
        
        # 计算处理时间
        elapsed_time = time.time() - start_time
        logger.info(f"视频合成完成 - 写入 {written_frames} 帧, 耗时: {elapsed_time:.2f} 秒")
        
        return output_path
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """获取视频信息
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            视频信息字典
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        # 打开视频
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {video_path}")
        
        # 获取视频信息
        info = {
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': cap.get(cv2.CAP_PROP_FPS),
            'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'duration': float('inf'),  # 将在下面计算
            'codec': int(cap.get(cv2.CAP_PROP_FOURCC)),
            'size': os.path.getsize(video_path)
        }
        
        # 计算视频时长
        if info['fps'] > 0:
            info['duration'] = info['frame_count'] / info['fps']
        
        # 释放资源
        cap.release()
        
        # 解码四字符编码 (FOURCC)
        info['codec_name'] = self._decode_fourcc(info['codec'])
        
        return info
    
    def _decode_fourcc(self, fourcc: int) -> str:
        """解码视频四字符编码
        
        Args:
            fourcc: 四字符编码整数
            
        Returns:
            解码后的四字符编码字符串
        """
        try:
            fourcc_code = ""
            for i in range(4):
                fourcc_code += chr((fourcc >> 8 * i) & 0xFF)
            return fourcc_code
        except:
            return "unknown"
    
    def split_video(self, video_path: str, output_dir: Optional[str] = None, segment_duration: float = 60.0) -> List[str]:
        """分割视频为多个片段
        
        Args:
            video_path: 视频文件路径
            output_dir: 输出目录
            segment_duration: 每个片段的时长（秒）
            
        Returns:
            分割后的视频文件路径列表
        """
        # 获取视频信息
        video_info = self.get_video_info(video_path)
        fps = video_info['fps']
        total_frames = video_info['frame_count']
        total_duration = video_info['duration']
        
        # 设置输出目录
        if output_dir is None:
            # 创建基于时间戳的临时目录
            timestamp = int(time.time())
            output_dir = os.path.join(self.temp_dir, f"video_segments_{timestamp}")
        
        ensure_directory(output_dir)
        
        logger.info(f"开始分割视频 - 时长: {total_duration:.2f}秒, 每段: {segment_duration:.2f}秒")
        
        # 计算片段数量
        segment_count = max(1, int(total_duration / segment_duration))
        frames_per_segment = int(fps * segment_duration)
        
        # 分割视频
        cap = cv2.VideoCapture(video_path)
        
        segment_paths = []
        
        for i in range(segment_count):
            # 计算片段的起始和结束帧
            start_frame = i * frames_per_segment
            end_frame = min((i + 1) * frames_per_segment, total_frames)
            
            # 设置输出文件名
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            segment_filename = f"{video_name}_segment_{i+1:04d}.mp4"
            segment_path = os.path.join(output_dir, segment_filename)
            
            # 创建视频写入器
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(segment_path, fourcc, fps, (video_info['width'], video_info['height']))
            
            # 跳转到起始帧
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            
            # 写入片段
            frame_count = 0
            while True:
                ret, frame = cap.read()
                if not ret or cap.get(cv2.CAP_PROP_POS_FRAMES) >= end_frame:
                    break
                
                out.write(frame)
                frame_count += 1
            
            # 释放写入器
            out.release()
            
            # 记录片段路径
            segment_paths.append(segment_path)
            logger.debug(f"创建视频片段: {segment_path}, 帧数: {frame_count}")
        
        # 释放视频读取器
        cap.release()
        
        logger.info(f"视频分割完成 - 创建了 {len(segment_paths)} 个片段")
        
        return segment_paths
    
    def clean_temp_files(self, older_than_hours: int = 24) -> int:
        """清理临时文件
        
        Args:
            older_than_hours: 清理多少小时之前的文件
            
        Returns:
            清理的文件数量
        """
        from ..utils.file_utils import clean_temp_files as _clean_temp_files
        
        logger.info(f"清理临时文件 - 目录: {self.temp_dir}, 时间: {older_than_hours}小时")
        count = _clean_temp_files(self.temp_dir, older_than=older_than_hours)
        logger.info(f"清理了 {count} 个临时文件")
        return count