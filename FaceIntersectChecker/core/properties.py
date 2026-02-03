"""
相交检测器属性定义
"""

import bpy
from bpy.props import BoolProperty, FloatProperty, EnumProperty, FloatVectorProperty
from . import mesh_helpers


def update_color_display(self, context):
    """更新颜色显示状态的回调函数"""
    if self.show_color_display:
        # 启用颜色显示
        if mesh_helpers.get_intersection_stats()['objects_count'] > 0:
            mesh_helpers.enable_display()
    else:
        # 禁用颜色显示
        mesh_helpers.disable_display()

class IntersectionDetectorProperties(bpy.types.PropertyGroup):
    """相交检测器属性组"""
    
    # 检测类型选择
    detection_type: EnumProperty( #type: ignore
        name="检测类型",
        description="选择相交检测的类型",
        items=[
            ('SELF', "自相交", "检测单个网格的自相交问题"),
            ('OBJECTS', "对象间相交", "检测多个对象之间的相交"),
            ('BOTH', "全面检测", "同时检测自相交和对象间相交"),
        ],
        default='SELF'
    )
    
    # 显示控制
    show_color_display: BoolProperty(  #type: ignore
        name="颜色显示",
        description="在视口中显示相交区域的颜色高亮",
        default=True,
        update=update_color_display
    )
    
    auto_update: BoolProperty(  #type: ignore
        name="自动更新",
        description="编辑网格时自动更新相交检测",
        default=False
    )
    
    # 颜色配置
    intersect_face_color: FloatVectorProperty(  #type: ignore
        name="相交面颜色",
        description="相交面的显示颜色",
        default=(0.96, 0.25, 0.006, 0.6),
        size=4,
        subtype='COLOR',
        min=0.0,
        max=1.0
    )
    
    intersect_edge_color: FloatVectorProperty(  #type: ignore
        name="相交边颜色", 
        description="相交边的显示颜色",
        default=(1.0, 0.5, 0.0, 0.8),
        size=4,
        subtype='COLOR',
        min=0.0,
        max=1.0
    )
    
    # 检测参数
    intersect_threshold: FloatProperty(  #type: ignore
        name="相交阈值",
        description="相交检测的距离阈值",
        default=0.00001,
        min=0.000001,
        max=0.01,
        precision=6
    )
    
    # 统计信息
    last_check_results: bpy.props.StringProperty(  #type: ignore
        name="最后检测结果",
        description="最后一次检测的结果信息",
        default="尚未检测"
    )


def register():
    """注册属性"""
    bpy.utils.register_class(IntersectionDetectorProperties)
    bpy.types.Scene.intersection_detector = bpy.props.PointerProperty(type=IntersectionDetectorProperties)  #type: ignore


def unregister():
    """注销属性"""
    del bpy.types.Scene.intersection_detector
    bpy.utils.unregister_class(IntersectionDetectorProperties)