"""日志管理模块

提供日志设置和获取功能，支持不同级别的日志输出和文件记录。
"""

import logging
import os
import sys
from typing import Optional
from datetime import datetime

# 全局日志配置
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
CONSOLE_FORMAT = '%(name)s - %(levelname)s - %(message)s'

# 日志级别映射
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'WARN': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

# 全局日志器字典
_loggers = {}


def setup_logger(
    name: str = 'video_keev',
    level: str = 'INFO',
    log_file: Optional[str] = None,
    console_level: Optional[str] = None,
    file_level: Optional[str] = None
) -> logging.Logger:
    """设置日志器
    
    创建并配置一个日志器，支持控制台和文件输出。
    
    Args:
        name: 日志器名称
        level: 默认日志级别
        log_file: 日志文件路径
        console_level: 控制台输出级别，如果为None则使用默认级别
        file_level: 文件输出级别，如果为None则使用默认级别
        
    Returns:
        配置好的日志器实例
    """
    # 如果日志器已存在，则返回现有实例
    if name in _loggers:
        return _loggers[name]
    
    # 创建日志器
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVELS.get(level.upper(), logging.INFO))
    logger.propagate = False
    
    # 清理现有的处理器
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 设置控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(LOG_LEVELS.get(console_level.upper() if console_level else level.upper(), logging.INFO))
    console_formatter = logging.Formatter(CONSOLE_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 设置文件处理器（如果指定了日志文件）
    if log_file:
        # 确保日志文件目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 创建文件处理器
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(LOG_LEVELS.get(file_level.upper() if file_level else level.upper(), logging.INFO))
        file_formatter = logging.Formatter(LOG_FORMAT)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # 保存到全局字典
    _loggers[name] = logger
    
    return logger


def get_logger(name: str = 'video_keev') -> logging.Logger:
    """获取日志器
    
    如果日志器不存在，则创建一个默认配置的日志器。
    
    Args:
        name: 日志器名称
        
    Returns:
        日志器实例
    """
    if name not in _loggers:
        # 创建默认配置的日志器
        return setup_logger(name)
    return _loggers[name]


def log_with_context(logger: logging.Logger, level: int, message: str, **context) -> None:
    """带上下文的日志记录
    
    在日志消息中添加上下文信息。
    
    Args:
        logger: 日志器实例
        level: 日志级别
        message: 日志消息
        **context: 上下文信息
    """
    # 构建上下文字符串
    context_str = ' '.join([f'{k}={v}' for k, v in context.items()])
    full_message = f"{message} [{context_str}]" if context_str else message
    
    # 记录日志
    logger.log(level, full_message)


def log_error_with_traceback(logger: logging.Logger, message: str, exception: Exception) -> None:
    """记录带异常堆栈的错误日志
    
    Args:
        logger: 日志器实例
        message: 错误消息
        exception: 异常实例
    """
    logger.error(message, exc_info=exception)


def setup_rotating_logger(
    name: str = 'video_keev',
    log_file: str = 'video_keev.log',
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 5,
    level: str = 'INFO'
) -> logging.Logger:
    """设置轮转日志器
    
    创建一个支持文件轮转的日志器。
    
    Args:
        name: 日志器名称
        log_file: 日志文件路径
        max_bytes: 单个日志文件最大字节数
        backup_count: 保留的备份文件数
        level: 日志级别
        
    Returns:
        配置好的日志器实例
    """
    import logging.handlers
    
    # 创建日志器
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVELS.get(level.upper(), logging.INFO))
    logger.propagate = False
    
    # 清理现有的处理器
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 设置轮转文件处理器
    handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    formatter = logging.Formatter(LOG_FORMAT)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # 设置控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(CONSOLE_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 保存到全局字典
    _loggers[name] = logger
    
    return logger

# 默认日志器
default_logger = setup_logger()