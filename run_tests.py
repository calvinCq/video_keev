#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
视频复刻工具测试执行脚本

此脚本用于设置测试环境并运行完整的视频复刻工作流测试。
它会自动处理环境变量设置、依赖检查，并执行测试套件。
"""

import os
import sys
import subprocess
import time
import logging
from pathlib import Path

# 尝试从.env文件加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
    logging.info("成功从.env文件加载环境变量")
except ImportError:
    logging.warning("未安装python-dotenv库，无法从.env文件加载环境变量")

# 设置日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_run.log')
    ]
)

logger = logging.getLogger('test_runner')


def check_environment():
    """检查测试环境"""
    logger.info("开始检查测试环境...")
    
    # 检查Python版本
    python_version = sys.version_info
    logger.info(f"Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # 检查必要的环境变量
    if 'COMFYUI_API_ENDPOINT' not in os.environ:
        logger.warning("未设置COMFYUI_API_ENDPOINT环境变量，使用默认值")
        os.environ['COMFYUI_API_ENDPOINT'] = 'http://localhost:8188'
    
    if 'COMFYUI_API_KEY' not in os.environ:
        logger.warning("未设置COMFYUI_API_KEY环境变量，使用空值")
        os.environ['COMFYUI_API_KEY'] = ''
    
    # 检查必要的目录
    for dir_name in ['tests', 'src']:
        if not os.path.exists(dir_name):
            logger.error(f"目录 {dir_name} 不存在")
            return False
    
    # 检查requirements.txt文件
    if not os.path.exists('requirements.txt'):
        logger.error("requirements.txt文件不存在")
        return False
    
    logger.info("测试环境检查完成")
    return True


def install_dependencies():
    """安装测试依赖"""
    logger.info("开始安装测试依赖...")
    
    try:
        # 安装requirements.txt中的依赖
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        logger.info("测试依赖安装完成")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"安装依赖失败: {e.stderr.decode('utf-8', errors='replace')}")
        return False


def test_comfyui_connection():
    """测试ComfyUI API连接"""
    logger.info(f"开始测试ComfyUI API连接: {os.environ['COMFYUI_API_ENDPOINT']}")
    
    try:
        import requests
        
        # 测试ComfyUI API连接
        response = requests.get(
            f"{os.environ['COMFYUI_API_ENDPOINT']}/prompt",
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info("ComfyUI API连接成功")
            return True
        else:
            logger.warning(f"ComfyUI API连接返回非200状态码: {response.status_code}")
            logger.warning("测试将继续，但可能会因为API连接问题而失败")
            return False
    except requests.RequestException as e:
        logger.warning(f"ComfyUI API连接失败: {str(e)}")
        logger.warning("测试将继续，但可能会因为API连接问题而失败")
        return False


def run_tests():
    """运行测试套件"""
    logger.info("开始运行测试套件...")
    
    # 运行测试文件
    test_file = Path('tests/test_full_workflow.py')
    
    if not test_file.exists():
        logger.error(f"测试文件不存在: {test_file}")
        return False
    
    try:
        # 运行测试
        process = subprocess.Popen(
            [sys.executable, str(test_file)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 实时输出测试进度
        stdout_lines = []
        stderr_lines = []
        
        while True:
            # 读取标准输出
            for line in process.stdout:
                line = line.strip()
                print(line)
                stdout_lines.append(line)
                
            # 读取标准错误
            for line in process.stderr:
                line = line.strip()
                print(line, file=sys.stderr)
                stderr_lines.append(line)
            
            # 检查进程是否结束
            if process.poll() is not None:
                break
            
            # 短暂休眠避免CPU占用过高
            time.sleep(0.1)
        
        # 等待进程完全结束
        process.wait()
        
        # 检查测试是否成功
        if process.returncode == 0:
            logger.info("测试套件运行成功")
            return True
        else:
            logger.error(f"测试套件运行失败，返回码: {process.returncode}")
            return False
            
    except Exception as e:
        logger.error(f"运行测试时发生异常: {str(e)}")
        return False


def generate_test_report(success):
    """生成测试报告"""
    logger.info("生成测试报告...")
    
    report_path = Path('test_report.txt')
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("视频复刻工具测试报告\n")
        f.write("=" * 50 + "\n\n")
        
        f.write(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"ComfyUI API端点: {os.environ['COMFYUI_API_ENDPOINT']}\n")
        f.write(f"测试结果: {'成功' if success else '失败'}\n\n")
        
        # 添加测试建议
        f.write("测试建议:\n")
        f.write("1. 确保ComfyUI服务正在运行\n")
        f.write("2. 检查API端点和密钥配置是否正确\n")
        f.write("3. 对于替换功能测试，建议使用包含明确人物、背景和商品的视频\n")
        f.write("4. 测试过程中可以监控ComfyUI的控制台输出以获取更多信息\n")
    
    logger.info(f"测试报告已生成: {report_path}")


def main():
    """主函数"""
    print("=" * 60)
    print("        视频复刻工具完整工作流测试        ")
    print("=" * 60)
    print()
    
    try:
        # 1. 检查环境
        if not check_environment():
            print("❌ 环境检查失败")
            return 1
        
        print("✅ 环境检查完成")
        
        # 2. 安装依赖
        if not install_dependencies():
            print("❌ 依赖安装失败")
            return 1
        
        print("✅ 依赖安装完成")
        
        # 3. 测试ComfyUI连接
        comfyui_connected = test_comfyui_connection()
        if not comfyui_connected:
            print("⚠️  ComfyUI连接测试失败，测试可能会受到影响")
        else:
            print("✅ ComfyUI连接测试成功")
        
        # 4. 运行测试
        print("\n开始运行测试...\n")
        test_success = run_tests()
        
        # 5. 生成报告
        generate_test_report(test_success)
        
        # 6. 输出最终结果
        print("\n" + "=" * 60)
        if test_success:
            print("✅ 所有测试成功完成！")
            print(f"📋 详细报告已保存至: test_report.txt")
            return 0
        else:
            print("❌ 测试执行失败！")
            print(f"📋 错误详情请查看: test_report.txt 和 test_run.log")
            return 1
            
    except KeyboardInterrupt:
        print("\n❌ 测试被用户中断")
        return 1
    except Exception as e:
        print(f"\n❌ 测试执行过程中发生未预期的错误: {str(e)}")
        return 1


if __name__ == '__main__':
    sys.exit(main())