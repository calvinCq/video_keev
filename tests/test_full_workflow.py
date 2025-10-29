#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
视频复刻工具完整工作流测试

此测试文件用于测试视频复刻工具的完整工作流程，包括：
1. 视频帧提取
2. 帧预处理
3. 替换功能（人物、背景、商品）
4. ComfyUI API交互
5. 处理后帧的合成

注意：此测试需要真实的视频文件和可用的ComfyUI API端点。
"""

import os
import sys
import time
import tempfile
import shutil
import unittest
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.workflow.manager import WorkflowManager
from src.config.manager import ConfigManager
from src.video.processor import VideoProcessor
from src.api.client import ComfyUIClient
from src.utils.logger import get_logger

# 配置测试日志
logger = get_logger(__name__)


class TestFullVideoReplicationWorkflow(unittest.TestCase):
    """视频复刻完整工作流测试类"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        cls.test_dir = tempfile.mkdtemp(prefix='video_keev_test_')
        cls.test_video_path = os.path.join(cls.test_dir, 'test_video.mp4')
        cls.output_dir = os.path.join(cls.test_dir, 'outputs')
        cls.temp_dir = os.path.join(cls.test_dir, 'temp')
        
        # 创建测试目录
        os.makedirs(cls.output_dir, exist_ok=True)
        os.makedirs(cls.temp_dir, exist_ok=True)
        
        # 创建配置管理器
        cls.config_manager = ConfigManager()
        
        # 使用字典直接访问配置，避免使用不存在的set方法
        cls.config_manager.config['video'] = {
            'temp_dir': cls.temp_dir,
            'output_dir': cls.output_dir
        }
        
        # 尝试从环境变量获取ComfyUI端点信息
        comfyui_endpoint = os.environ.get('COMFYUI_API_ENDPOINT', 'http://localhost:8188')
        comfyui_api_key = os.environ.get('COMFYUI_API_KEY', '')
        
        # 使用字典直接访问配置，避免使用不存在的set方法
        cls.config_manager.config['comfyui'] = {
            'api_endpoint': comfyui_endpoint,
            'api_key': comfyui_api_key
        }
        
        # 创建一个简单的测试视频（10帧，RGB颜色渐变）
        cls._create_test_video()
        
        logger.info(f"测试环境设置完成: {cls.test_dir}")
    
    @classmethod
    def tearDownClass(cls):
        """清理测试环境"""
        # 清理临时文件
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)
        logger.info(f"测试环境清理完成: {cls.test_dir}")
    
    @classmethod
    def _create_test_video(cls):
        """创建一个简单的测试视频用于测试"""
        try:
            import cv2
            import numpy as np
            
            # 创建一个简单的测试视频（10帧，RGB颜色渐变）
            width, height = 320, 240
            fps = 10
            frame_count = 10
            
            # 定义编码器并创建VideoWriter对象
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(cls.test_video_path, fourcc, fps, (width, height))
            
            # 生成渐变帧
            for i in range(frame_count):
                # 创建一个渐变帧
                frame = np.zeros((height, width, 3), dtype=np.uint8)
                
                # 红色通道从左到右渐变
                for x in range(width):
                    red = int((x / width) * 255)
                    green = int((i / frame_count) * 255)
                    blue = int(((width - x) / width) * 255)
                    frame[:, x] = [blue, green, red]  # BGR格式
                
                # 添加一些形状作为"对象"供替换功能测试
                if i % 2 == 0:
                    # 添加一个圆形作为"人物"
                    cv2.circle(frame, (width//2, height//2), 30, (0, 255, 255), -1)
                else:
                    # 添加一个矩形作为"商品"
                    cv2.rectangle(frame, (width//3, height//3), (2*width//3, 2*height//3), (255, 0, 255), -1)
                
                # 写入帧
                out.write(frame)
            
            # 释放VideoWriter
            out.release()
            
            logger.info(f"测试视频创建成功: {cls.test_video_path}")
        except Exception as e:
            logger.error(f"创建测试视频失败: {str(e)}")
            raise
    
    def setUp(self):
        """每个测试用例的设置"""
        # 创建工作流管理器
        self.workflow_manager = WorkflowManager(self.config_manager)
        
        # 创建基本工作流配置
        self.base_workflow_config = {
            'video': {
                'fps': 10,
                'width': 320,
                'height': 240,
                'preview_mode': True,  # 测试模式只处理少量帧
                'preview_frames': 5
            },
            'preprocess': {
                'resize_width': 512,
                'resize_height': 512,
                'enhance_features': False,
                'preserve_details': False
            }
        }
    
    def test_basic_workflow(self):
        """测试基本视频复刻工作流"""
        logger.info("开始测试基本工作流")
        
        try:
            # 执行基本工作流
            workflow_info = self.workflow_manager.start_workflow(
                input_video=self.test_video_path,
                workflow_config=self.base_workflow_config
            )
            output_path = workflow_info.get('output_video')
            
            # 验证输出文件存在
            self.assertTrue(os.path.exists(output_path), "输出视频文件应该存在")
            logger.info(f"基本工作流测试成功，输出文件: {output_path}")
        except Exception as e:
            logger.error(f"基本工作流测试失败: {str(e)}")
            self.fail(f"基本工作流测试失败: {str(e)}")
    
    def test_person_replacement(self):
        """测试人物替换功能"""
        logger.info("开始测试人物替换功能")
        
        try:
            # 创建包含人物替换配置的工作流
            workflow_config = self.base_workflow_config.copy()
            workflow_config['replacement'] = {
                'enabled': True,
                'person': {
                    'enabled': True,
                    'prompt': "一个穿着蓝色衣服的人",
                    'preserve_pose': True,
                    'confidence_threshold': 0.6
                }
            }
            
            # 执行替换工作流
            workflow_info = self.workflow_manager.start_workflow(
                input_video=self.test_video_path,
                workflow_config=workflow_config
            )
            output_path = workflow_info.get('output_video')
            
            # 验证输出文件存在
            self.assertTrue(os.path.exists(output_path), "人物替换输出视频文件应该存在")
            logger.info(f"人物替换测试成功，输出文件: {output_path}")
        except Exception as e:
            logger.error(f"人物替换测试失败: {str(e)}")
            self.fail(f"人物替换测试失败: {str(e)}")
    
    def test_background_replacement(self):
        """测试背景替换功能"""
        logger.info("开始测试背景替换功能")
        
        try:
            # 创建包含背景替换配置的工作流
            workflow_config = self.base_workflow_config.copy()
            workflow_config['replacement'] = {
                'enabled': True,
                'background': {
                    'enabled': True,
                    'prompt': "蓝色渐变背景",
                    'preserve_foreground': True,
                    'confidence_threshold': 0.5
                },
                'preserve_lighting': True
            }
            
            # 执行替换工作流
            workflow_info = self.workflow_manager.start_workflow(
                input_video=self.test_video_path,
                workflow_config=workflow_config
            )
            output_path = workflow_info.get('output_video')
            
            # 验证输出文件存在
            self.assertTrue(os.path.exists(output_path), "背景替换输出视频文件应该存在")
            logger.info(f"背景替换测试成功，输出文件: {output_path}")
        except Exception as e:
            logger.error(f"背景替换测试失败: {str(e)}")
            self.fail(f"背景替换测试失败: {str(e)}")
    
    def test_product_replacement(self):
        """测试商品替换功能"""
        logger.info("开始测试商品替换功能")
        
        try:
            # 创建包含商品替换配置的工作流
            workflow_config = self.base_workflow_config.copy()
            workflow_config['replacement'] = {
                'enabled': True,
                'product': {
                    'enabled': True,
                    'prompt': "一个红色的方形物体",
                    'confidence_threshold': 0.6
                }
            }
            
            # 执行替换工作流
            workflow_info = self.workflow_manager.start_workflow(
                input_video=self.test_video_path,
                workflow_config=workflow_config
            )
            output_path = workflow_info.get('output_video')
            
            # 验证输出文件存在
            self.assertTrue(os.path.exists(output_path), "商品替换输出视频文件应该存在")
            logger.info(f"商品替换测试成功，输出文件: {output_path}")
        except Exception as e:
            logger.error(f"商品替换测试失败: {str(e)}")
            self.fail(f"商品替换测试失败: {str(e)}")
    
    def test_combined_replacements(self):
        """测试组合替换功能（人物+背景+商品）"""
        logger.info("开始测试组合替换功能")
        
        try:
            # 创建包含所有替换类型的工作流
            workflow_config = self.base_workflow_config.copy()
            workflow_config['replacement'] = {
                'enabled': True,
                'person': {
                    'enabled': True,
                    'prompt': "一个穿着黄色衣服的人",
                    'preserve_pose': True,
                    'confidence_threshold': 0.6
                },
                'background': {
                    'enabled': True,
                    'prompt': "绿色渐变背景",
                    'preserve_foreground': True,
                    'confidence_threshold': 0.5
                },
                'product': {
                    'enabled': True,
                    'prompt': "一个紫色的圆形物体",
                    'confidence_threshold': 0.6
                },
                'preserve_lighting': True
            }
            
            # 执行组合替换工作流
            workflow_info = self.workflow_manager.start_workflow(
                input_video=self.test_video_path,
                workflow_config=workflow_config
            )
            output_path = workflow_info.get('output_video')
            
            # 验证输出文件存在
            self.assertTrue(os.path.exists(output_path), "组合替换输出视频文件应该存在")
            logger.info(f"组合替换测试成功，输出文件: {output_path}")
        except Exception as e:
            logger.error(f"组合替换测试失败: {str(e)}")
            self.fail(f"组合替换测试失败: {str(e)}")


def run_all_tests():
    """运行所有测试"""
    logger.info("开始运行视频复刻工具完整工作流测试")
    
    # 创建测试套件
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestFullVideoReplicationWorkflow)
    
    # 运行测试
    unittest.TextTestRunner(verbosity=2).run(test_suite)
    
    logger.info("视频复刻工具完整工作流测试完成")


if __name__ == '__main__':
    # 直接运行测试
    run_all_tests()