"""视频复刻项目主入口

提供命令行界面和API入口，启动视频复刻工作流。
"""

import os
import sys
import argparse
import json
from datetime import datetime
from typing import Optional
from pathlib import Path

from .config.manager import ConfigManager
from .workflow.manager import WorkflowManager
from .utils.logger import setup_logger, get_logger
from .utils.file_utils import ensure_directory

# 设置日志
logger = get_logger(__name__)


def setup_environment() -> None:
    """设置运行环境"""
    # 确保必要的目录存在
    config = ConfigManager()
    ensure_directory(config.get('video.temp_dir'))
    ensure_directory(config.get('video.output_dir'))
    ensure_directory(config.get('logs.output_dir'))
    
    logger.info("环境设置完成")


def parse_arguments() -> argparse.Namespace:
    """解析命令行参数
    
    Returns:
        解析后的参数对象
    """
    parser = argparse.ArgumentParser(description='视频复刻工具 - 基于云端ComfyUI服务')
    
    # 子命令
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 复制视频命令
    replicate_parser = subparsers.add_parser('replicate', help='执行视频复刻')
    replicate_parser.add_argument('-i', '--input', required=True, help='输入视频文件路径')
    replicate_parser.add_argument('-o', '--output', help='输出视频文件路径')
    replicate_parser.add_argument('-w', '--workflow', help='工作流ID或配置文件路径')
    replicate_parser.add_argument('-f', '--frame-rate', type=float, help='处理帧率')
    replicate_parser.add_argument('-m', '--max-frames', type=int, help='最大处理帧数')
    replicate_parser.add_argument('-q', '--quality-level', choices=['low', 'medium', 'high'], default='high', help='质量级别')
    replicate_parser.add_argument('-p', '--poll-interval', type=int, default=5, help='状态轮询间隔（秒）')
    
    # 替换功能参数
    replicate_parser.add_argument('--enable-replacement', action='store_true', help='启用替换功能')
    replicate_parser.add_argument('--person-replacement', action='store_true', help='启用人物替换')
    replicate_parser.add_argument('--background-replacement', action='store_true', help='启用背景替换')
    replicate_parser.add_argument('--product-replacement', action='store_true', help='启用商品替换')
    replicate_parser.add_argument('--person-prompt', default=None, help='人物替换描述提示词')
    replicate_parser.add_argument('--background-prompt', default=None, help='背景替换描述提示词')
    replicate_parser.add_argument('--product-prompt', default=None, help='商品替换描述提示词')
    replicate_parser.add_argument('--person-image', default=None, help='人物替换参考图像路径')
    replicate_parser.add_argument('--background-image', default=None, help='背景替换参考图像路径')
    replicate_parser.add_argument('--product-image', default=None, help='商品替换参考图像路径')
    replicate_parser.add_argument('--preserve-pose', action='store_true', help='保留人物姿势（人物替换时）')
    replicate_parser.add_argument('--preserve-foreground', action='store_true', help='保留前景细节（背景替换时）')
    replicate_parser.add_argument('--preserve-lighting', action='store_true', help='保留光照效果')
    
    # 列出工作流命令
    list_parser = subparsers.add_parser('list-workflows', help='列出可用的工作流')
    
    # 查看状态命令
    status_parser = subparsers.add_parser('status', help='查看工作流状态')
    status_parser.add_argument('-w', '--workflow-id', help='工作流ID')
    
    # 取消工作流命令
    cancel_parser = subparsers.add_parser('cancel', help='取消工作流')
    cancel_parser.add_argument('-w', '--workflow-id', required=True, help='工作流ID')
    
    # 测试连接命令
    test_parser = subparsers.add_parser('test-connection', help='测试ComfyUI连接')
    
    # 默认命令
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    return parser.parse_args()


def load_workflow_config(workflow_arg: Optional[str]) -> dict:
    """加载工作流配置
    
    Args:
        workflow_arg: 工作流参数，可以是ID或配置文件路径
        
    Returns:
        工作流配置字典
    """
    config = {}
    
    if not workflow_arg:
        return config
    
    # 尝试作为文件路径加载
    if os.path.exists(workflow_arg):
        try:
            with open(workflow_arg, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"从文件加载工作流配置: {workflow_arg}")
        except Exception as e:
            logger.error(f"加载工作流配置文件失败: {str(e)}")
            # 如果加载失败，尝试作为工作流ID
            config['workflow_id'] = workflow_arg
    else:
        # 作为工作流ID
        config['workflow_id'] = workflow_arg
    
    return config


def cmd_replicate(args: argparse.Namespace) -> None:
    """执行视频复刻命令
    
    Args:
        args: 命令行参数
    """
    try:
        # 验证输入文件
        if not os.path.exists(args.input):
            logger.error(f"输入文件不存在: {args.input}")
            sys.exit(1)
        
        # 加载配置
        workflow_config = load_workflow_config(args.workflow)
        
        # 添加命令行参数
        if args.frame_rate:
            workflow_config['frame_rate'] = args.frame_rate
        if args.max_frames:
            workflow_config['max_frames'] = args.max_frames
        if args.quality_level:
            workflow_config.setdefault('params', {})['quality_level'] = args.quality_level
        if args.poll_interval:
            workflow_config['poll_interval'] = args.poll_interval
        if args.output:
            # 创建输出目录
            output_dir = os.path.dirname(args.output)
            if output_dir and not os.path.exists(output_dir):
                ensure_directory(output_dir)
        
        # 配置替换功能
        if args.enable_replacement or args.person_replacement or args.background_replacement or args.product_replacement:
            # 确保replacement配置存在
            if 'replacement' not in workflow_config:
                workflow_config['replacement'] = {
                    'enabled': True,
                    'person': {},
                    'background': {},
                    'product': {}
                }
            else:
                workflow_config['replacement']['enabled'] = True
            
            # 配置人物替换
            if args.person_replacement:
                workflow_config['replacement']['person'] = {
                    'enabled': True,
                    'prompt': args.person_prompt or "",
                    'reference_image': args.person_image,
                    'preserve_pose': args.preserve_pose,
                    'confidence_threshold': 0.7
                }
            
            # 配置背景替换
            if args.background_replacement:
                workflow_config['replacement']['background'] = {
                    'enabled': True,
                    'prompt': args.background_prompt or "",
                    'reference_image': args.background_image,
                    'preserve_foreground': args.preserve_foreground,
                    'confidence_threshold': 0.6
                }
            
            # 配置商品替换
            if args.product_replacement:
                workflow_config['replacement']['product'] = {
                    'enabled': True,
                    'prompt': args.product_prompt or "",
                    'reference_image': args.product_image,
                    'confidence_threshold': 0.7
                }
            
            # 全局替换选项
            if args.preserve_lighting:
                workflow_config['replacement']['preserve_lighting'] = True
            
            logger.info(f"已配置替换功能: 人物={args.person_replacement}, 背景={args.background_replacement}, 商品={args.product_replacement}")
        
        logger.info(f"开始视频复刻: {args.input}")
        logger.debug(f"工作流配置: {workflow_config}")
        
        # 创建工作流管理器
        workflow_manager = WorkflowManager()
        
        try:
            # 启动工作流
            result = workflow_manager.start_workflow(args.input, workflow_config)
            
            # 如果指定了输出路径，重命名输出文件
            if args.output and os.path.exists(workflow_manager.output_video_path):
                import shutil
                shutil.move(workflow_manager.output_video_path, args.output)
                result['output_video'] = args.output
            
            # 输出结果
            print(f"\n视频复刻完成！")
            print(f"工作流ID: {result['workflow_id']}")
            print(f"输入视频: {result['input_video']}")
            print(f"输出视频: {result['output_video']}")
            print(f"开始时间: {result['started_at']}")
            
            # 如果启用了替换功能，显示替换信息
            if workflow_config.get('replacement', {}).get('enabled', False):
                replacement_info = []
                if workflow_config.get('replacement', {}).get('person', {}).get('enabled', False):
                    replacement_info.append("人物替换")
                if workflow_config.get('replacement', {}).get('background', {}).get('enabled', False):
                    replacement_info.append("背景替换")
                if workflow_config.get('replacement', {}).get('product', {}).get('enabled', False):
                    replacement_info.append("商品替换")
                
                if replacement_info:
                    print(f"\n🔄 已应用替换: {', '.join(replacement_info)}")
            
            logger.info(f"视频复刻成功完成: {result['output_video']}")
            
        finally:
            # 清理资源
            workflow_manager.cleanup()
            
    except KeyboardInterrupt:
        logger.info("用户中断操作")
        sys.exit(0)
    except Exception as e:
        logger.error(f"视频复刻失败: {str(e)}", exc_info=True)
        print(f"\n错误: {str(e)}")
        sys.exit(1)


def cmd_list_workflows(_: argparse.Namespace) -> None:
    """列出可用工作流命令
    
    Args:
        _: 命令行参数
    """
    try:
        workflow_manager = WorkflowManager()
        
        print("\n可用工作流列表:")
        print("-" * 60)
        print(f"{'ID':<30} {'名称':<15} {'来源':<10}")
        print("-" * 60)
        
        workflows = workflow_manager.list_available_workflows()
        for wf in workflows:
            print(f"{wf['id']:<30} {wf['name']:<15} {wf['source']:<10}")
        
        print("-" * 60)
        print(f"共 {len(workflows)} 个工作流可用\n")
        
    except Exception as e:
        logger.error(f"获取工作流列表失败: {str(e)}")
        print(f"错误: {str(e)}")
        sys.exit(1)


def cmd_status(args: argparse.Namespace) -> None:
    """查看工作流状态命令
    
    Args:
        args: 命令行参数
    """
    # 注意：这里简化了实现，实际应该从持久化存储中获取工作流状态
    print("\n工作流状态功能需要实现持久化存储")
    print("当前版本暂不支持查看历史工作流状态\n")


def cmd_cancel(args: argparse.Namespace) -> None:
    """取消工作流命令
    
    Args:
        args: 命令行参数
    """
    # 注意：这里简化了实现，实际应该从持久化存储中获取工作流实例
    print("\n取消工作流功能需要实现持久化存储")
    print("当前版本暂不支持取消历史工作流\n")


def cmd_test_connection(_: argparse.Namespace) -> None:
    """测试ComfyUI连接命令
    
    Args:
        _: 命令行参数
    """
    try:
        from .api.client import ComfyUIClient
        
        config = ConfigManager()
        client = ComfyUIClient(
            api_endpoint=config.get('comfyui.api_endpoint'),
            api_key=os.getenv('COMFYUI_API_KEY')
        )
        
        print("\n正在测试ComfyUI连接...")
        
        if client.test_connection():
            print("✓ 连接成功！可以访问ComfyUI服务")
            
            # 获取服务信息
            info = client.get_server_info()
            if info:
                print(f"\n服务信息:")
                print(f"  版本: {info.get('version', '未知')}")
                print(f"  状态: {info.get('status', '未知')}")
                print(f"  工作流数量: {len(info.get('available_workflows', []))}")
            
        else:
            print("✗ 连接失败！无法访问ComfyUI服务")
            print(f"检查端点: {config.get('comfyui.api_endpoint')}")
            
    except Exception as e:
        logger.error(f"连接测试失败: {str(e)}")
        print(f"错误: {str(e)}")
        sys.exit(1)


def main() -> None:
    """主函数"""
    try:
        # 设置环境
        setup_environment()
        
        # 解析参数
        args = parse_arguments()
        
        # 执行相应命令
        if args.command == 'replicate':
            cmd_replicate(args)
        elif args.command == 'list-workflows':
            cmd_list_workflows(args)
        elif args.command == 'status':
            cmd_status(args)
        elif args.command == 'cancel':
            cmd_cancel(args)
        elif args.command == 'test-connection':
            cmd_test_connection(args)
        
    except Exception as e:
        logger.error(f"程序执行失败: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()