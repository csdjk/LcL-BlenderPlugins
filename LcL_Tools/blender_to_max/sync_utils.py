"""
SyncBlender 同步工具
用于与Max进行数据交换的实用工具
"""

import bpy
import os
import tempfile

# 常量定义
SYNCBLENDER_EXCHANGE_FOLDER = "SyncBlender_Exchange"
FBX_FILENAME = "export_model.fbx"


def get_syncblender_exchange_path():
    """获取SyncBlender交换目录路径"""
    temp_dir = tempfile.gettempdir()
    exchange_dir = os.path.join(temp_dir, SYNCBLENDER_EXCHANGE_FOLDER)
    return exchange_dir


def get_fbx_import_path():
    """获取FBX导入文件的完整路径"""
    exchange_dir = get_syncblender_exchange_path()
    fbx_path = os.path.join(exchange_dir, FBX_FILENAME)
    return fbx_path


def import_fbx_from_max():
    """
    快速导入来自Max的FBX模型
    
    Returns:
        bool: 导入是否成功
    """
    # 使用操作符导入FBX
    result = bpy.ops.import_scene.syncblender_import_fbx()
    return result == {'FINISHED'}


def check_fbx_file_exists():
    """
    检查FBX文件是否存在
    
    Returns:
        bool: 文件是否存在
    """
    fbx_path = get_fbx_import_path()
    return os.path.exists(fbx_path)


def get_fbx_file_info():
    """
    获取FBX文件信息
    
    Returns:
        dict: 文件信息字典，包含路径、存在性、大小等
    """
    fbx_path = get_fbx_import_path()
    info = {
        'path': fbx_path,
        'exists': os.path.exists(fbx_path),
        'size': 0,
        'modified_time': None
    }
    
    if info['exists']:
        stat = os.stat(fbx_path)
        info['size'] = stat.st_size
        info['modified_time'] = stat.st_mtime
    
    return info


# 便利函数别名
import_max_fbx = import_fbx_from_max  # 别名，方便调用