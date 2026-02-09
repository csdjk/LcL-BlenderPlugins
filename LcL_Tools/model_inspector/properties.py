"""
模型检测器属性定义
"""

import bpy
import math
from bpy.props import BoolProperty, FloatProperty, EnumProperty, FloatVectorProperty
from . import mesh_helpers

# 自动更新处理器
_auto_update_handler = None


def update_display_based_on_checks(context):
    """根据检测功能开关状态更新显示"""
    if not hasattr(context.scene, 'model_inspector'):
        return
    
    props = context.scene.model_inspector
    stats = mesh_helpers.get_inspection_stats()
    
    # 如果有任何检测功能开启且有数据，则启用显示
    if ((props.check_intersection or props.check_distortion) and 
        stats['objects_count'] > 0):
        mesh_helpers.enable_display()
    else:
        mesh_helpers.disable_display()


def update_intersection_check(self, context):
    """相交检测开关回调"""
    update_display_based_on_checks(context)


def update_distortion_check_toggle(self, context):
    """扭曲检测开关回调"""
    update_display_based_on_checks(context)


def update_distortion_check(self, context):
    """扭曲检查参数更新回调"""
    # 如果自动更新开启，触发重新检查
    if hasattr(context.scene, 'model_inspector') and context.scene.model_inspector.auto_update:
        trigger_auto_update(context.scene)


def update_auto_update(self, context):
    """自动更新开关回调"""
    global _auto_update_handler
    
    if self.auto_update:
        # 启用自动更新
        if _auto_update_handler is None:
            bpy.app.handlers.frame_change_post.append(frame_change_handler)
            _auto_update_handler = frame_change_handler
            print("ModelInspector: 自动更新已启用")
    else:
        # 禁用自动更新
        if _auto_update_handler is not None:
            try:
                bpy.app.handlers.frame_change_post.remove(frame_change_handler)
                _auto_update_handler = None
                print("ModelInspector: 自动更新已禁用")
            except ValueError:
                # 处理器可能已经被移除
                _auto_update_handler = None


def frame_change_handler(scene):
    """帧变化处理器"""
    if hasattr(scene, 'model_inspector') and scene.model_inspector.auto_update:
        # 检查是否有任何检测功能开启
        props = scene.model_inspector
        if props.check_intersection or props.check_distortion:
            trigger_auto_update(scene)


def trigger_auto_update(scene):
    """触发自动更新检测"""
    try:
        props = scene.model_inspector
        
        # 根据开启的功能执行相应的检测
        if props.check_intersection and props.check_distortion:
            # 全面检测
            bpy.ops.mesh.model_inspector_check_all()
        elif props.check_intersection:
            # 仅相交检测
            if props.intersect_type == 'SELF':
                bpy.ops.mesh.model_inspector_check_self()
            elif props.intersect_type == 'OBJECTS':
                bpy.ops.mesh.model_inspector_check_objects()
            else:  # BOTH
                bpy.ops.mesh.model_inspector_check_all()
        elif props.check_distortion:
            # 仅扭曲检测
            bpy.ops.mesh.model_inspector_check_distortion()
            
    except Exception as e:
        # 静默处理错误，避免在动画播放时频繁报错
        pass


class ModelInspectorProperties(bpy.types.PropertyGroup):
    """模型检测器属性组"""
    
    # 相交检测开关
    check_intersection: BoolProperty( #type: ignore
        name="相交检测",
        description="启用相交检测功能",
        default=True,
        update=update_intersection_check
    )
    
    # 相交检测子类型
    intersect_type: EnumProperty( #type: ignore
        name="相交类型",
        description="选择相交检测的类型",
        items=[
            ('SELF', "自相交", "检测单个网格的自相交问题"),
            ('OBJECTS', "对象间相交", "检测多个对象之间的相交"),
            ('BOTH', "全面相交", "同时检测自相交和对象间相交"),
        ],
        default='SELF'
    )
    
    auto_update: BoolProperty(  #type: ignore
        name="自动更新",
        description="编辑网格时自动更新相交检测",
        default=False,
        update=update_auto_update
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
    
    # 扭曲检测属性
    check_distortion: BoolProperty(  #type: ignore
        name="启用扭曲检测",
        description="检查面片是否存在扭曲（非平面）",
        default=False,
        update=update_distortion_check_toggle
    )
    
    distortion_angle: FloatProperty(  #type: ignore
        name="扭曲角度阈值",
        description="检查扭曲面片的角度阈值",
        default=math.radians(45.0),
        min=0.0,
        max=math.radians(180.0),
        subtype='ANGLE',
        update=update_distortion_check
    )
    
    distortion_face_color: FloatVectorProperty(  #type: ignore
        name="扭曲面颜色",
        description="扭曲面片的显示颜色",
        default=(0.8, 0.4, 0.8, 0.6),
        size=4,
        subtype='COLOR',
        min=0.0,
        max=1.0
    )
    
    # 统计信息
    last_check_results: bpy.props.StringProperty(  #type: ignore
        name="最后检测结果",
        description="最后一次检测的结果信息",
        default="尚未检测"
    )
    
    # 最后检测的对象名称（用于显示）
    last_inspected_objects: bpy.props.StringProperty(  #type: ignore
        name="最后检测对象",
        description="最后一次检测的对象名称",
        default=""
    )


def register():
    """注册属性"""
    bpy.utils.register_class(ModelInspectorProperties)
    bpy.types.Scene.model_inspector = bpy.props.PointerProperty(type=ModelInspectorProperties)  #type: ignore


def unregister():
    """注销属性"""
    global _auto_update_handler
    
    # 清理自动更新处理器
    if _auto_update_handler is not None:
        try:
            bpy.app.handlers.frame_change_post.remove(frame_change_handler)
            _auto_update_handler = None
            print("ModelInspector: 自动更新处理器已清理")
        except ValueError:
            # 处理器可能已经被移除
            _auto_update_handler = None
    
    del bpy.types.Scene.model_inspector
    bpy.utils.unregister_class(ModelInspectorProperties)
