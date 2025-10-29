"""文件处理工具模块

提供目录创建、文件读写、临时文件清理等功能。
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional, Union
import hashlib


def ensure_directory(path: Union[str, Path]) -> None:
    """确保目录存在
    
    如果目录不存在，则创建该目录及其父目录。
    
    Args:
        path: 目录路径
    """
    Path(path).mkdir(parents=True, exist_ok=True)


def clean_temp_files(directory: Union[str, Path], pattern: Optional[str] = None, older_than: Optional[int] = None) -> int:
    """清理临时文件
    
    根据指定模式和时间清理临时目录中的文件。
    
    Args:
        directory: 临时目录路径
        pattern: 文件匹配模式，例如 '*.tmp'。如果为None，则清理所有文件
        older_than: 清理多少小时之前的文件。如果为None，则不考虑时间
        
    Returns:
        清理的文件数量
    """
    import glob
    import time
    
    directory_path = Path(directory)
    if not directory_path.exists() or not directory_path.is_dir():
        return 0
    
    count = 0
    current_time = time.time()
    
    # 确定要清理的文件路径
    if pattern:
        search_path = str(directory_path / pattern)
        files_to_clean = glob.glob(search_path)
    else:
        files_to_clean = [str(f) for f in directory_path.iterdir() if f.is_file()]
    
    # 清理文件
    for file_path in files_to_clean:
        file_stat = os.stat(file_path)
        
        # 检查文件年龄
        if older_than:
            file_age_hours = (current_time - file_stat.st_mtime) / 3600
            if file_age_hours < older_than:
                continue
        
        try:
            os.remove(file_path)
            count += 1
        except (OSError, IOError) as e:
            # 忽略删除错误，继续处理其他文件
            pass
    
    return count


def create_temp_directory(prefix: str = 'video_keev_') -> str:
    """创建临时目录
    
    Args:
        prefix: 临时目录前缀
        
    Returns:
        临时目录路径
    """
    return tempfile.mkdtemp(prefix=prefix)


def remove_directory(directory: Union[str, Path], ignore_errors: bool = True) -> None:
    """删除目录
    
    Args:
        directory: 要删除的目录路径
        ignore_errors: 是否忽略错误
    """
    if os.path.exists(directory):
        shutil.rmtree(directory, ignore_errors=ignore_errors)


def get_file_hash(file_path: Union[str, Path], algorithm: str = 'md5') -> str:
    """计算文件哈希值
    
    Args:
        file_path: 文件路径
        algorithm: 哈希算法，支持 'md5', 'sha1', 'sha256'
        
    Returns:
        文件哈希值（十六进制字符串）
    """
    hash_obj = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as f:
        # 分块读取文件
        for chunk in iter(lambda: f.read(4096), b''):
            hash_obj.update(chunk)
    
    return hash_obj.hexdigest()


def list_files(directory: Union[str, Path], pattern: Optional[str] = None, recursive: bool = False) -> List[str]:
    """列出目录中的文件
    
    Args:
        directory: 目录路径
        pattern: 文件匹配模式
        recursive: 是否递归搜索子目录
        
    Returns:
        文件路径列表
    """
    directory_path = Path(directory)
    if not directory_path.exists() or not directory_path.is_dir():
        return []
    
    if pattern:
        if recursive:
            return [str(p) for p in directory_path.glob(f'**/{pattern}') if p.is_file()]
        else:
            return [str(p) for p in directory_path.glob(pattern) if p.is_file()]
    else:
        if recursive:
            return [str(p) for p in directory_path.rglob('*') if p.is_file()]
        else:
            return [str(p) for p in directory_path.iterdir() if p.is_file()]


def safe_copy(src: Union[str, Path], dst: Union[str, Path], overwrite: bool = False) -> bool:
    """安全地复制文件
    
    Args:
        src: 源文件路径
        dst: 目标文件路径
        overwrite: 是否覆盖已存在的文件
        
    Returns:
        是否复制成功
    """
    src_path = Path(src)
    dst_path = Path(dst)
    
    # 检查源文件是否存在
    if not src_path.exists() or not src_path.is_file():
        return False
    
    # 检查目标文件是否存在
    if dst_path.exists():
        if not overwrite:
            return False
        # 如果目标是目录，则使用源文件名
        if dst_path.is_dir():
            dst_path = dst_path / src_path.name
    else:
        # 确保目标目录存在
        ensure_directory(dst_path.parent)
    
    try:
        shutil.copy2(src_path, dst_path)
        return True
    except (OSError, IOError):
        return False


def safe_move(src: Union[str, Path], dst: Union[str, Path], overwrite: bool = False) -> bool:
    """安全地移动文件
    
    Args:
        src: 源文件路径
        dst: 目标文件路径
        overwrite: 是否覆盖已存在的文件
        
    Returns:
        是否移动成功
    """
    src_path = Path(src)
    dst_path = Path(dst)
    
    # 检查源文件是否存在
    if not src_path.exists() or not src_path.is_file():
        return False
    
    # 检查目标文件是否存在
    if dst_path.exists():
        if not overwrite:
            return False
        # 如果目标是目录，则使用源文件名
        if dst_path.is_dir():
            dst_path = dst_path / src_path.name
    else:
        # 确保目标目录存在
        ensure_directory(dst_path.parent)
    
    try:
        shutil.move(src_path, dst_path)
        return True
    except (OSError, IOError):
        return False


def read_text_file(file_path: Union[str, Path]) -> Optional[str]:
    """读取文本文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件内容，如果文件不存在或读取失败则返回None
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except (OSError, IOError):
        return None


def write_text_file(file_path: Union[str, Path], content: str, overwrite: bool = True) -> bool:
    """写入文本文件
    
    Args:
        file_path: 文件路径
        content: 文件内容
        overwrite: 是否覆盖已存在的文件
        
    Returns:
        是否写入成功
    """
    file_path_obj = Path(file_path)
    
    # 检查文件是否存在
    if file_path_obj.exists() and not overwrite:
        return False
    
    # 确保目录存在
    ensure_directory(file_path_obj.parent)
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except (OSError, IOError):
        return False