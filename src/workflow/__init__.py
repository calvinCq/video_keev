"""工作流管理模块

负责协调整个视频复刻流程，包括任务执行、状态管理和进度跟踪。
"""

from .manager import WorkflowManager

__all__ = ["WorkflowManager"]