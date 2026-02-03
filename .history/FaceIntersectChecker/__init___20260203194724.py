"""
相交检测器 (Intersection Detector) - Blender 扩展
专业的网格相交检测和可视化工具

从 check_toolbox 中提取的相交检测功能，提供：
- 自相交检测
- 对象间相交检测  
- 实时颜色显示
- GPU 高性能渲染
"""

bl_info = {
    "name": "LcL Tools",
    "author": "LcL",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > LcL",
    "description": "LcL Tools (模型穿插检测)",
    "warning": "",
    "doc_url": "",
    "category": "Mesh",
}

import bpy
from . import core
from . import ui

def register():
    """注册扩展"""
    core.register()
    ui.register()
    
    print("相交检测器扩展已加载")

def unregister():
    """注销扩展"""
    # 清理 GPU 绘制句柄
    from .core import mesh_helpers
    mesh_helpers.cleanup_handlers()
    
    ui.unregister()
    core.unregister()
    
    print("相交检测器扩展已卸载")

if __name__ == "__main__":
    register()