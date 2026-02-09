"""
BlenderToMax同步属性定义
"""

import bpy
from bpy.types import PropertyGroup
from bpy.props import BoolProperty, EnumProperty, FloatProperty


class BlenderToMaxSettings(PropertyGroup):
    """BlenderToMax设置属性组"""
    
    # 导出范围设置
    export_scope: EnumProperty(
        name="导出范围",
        description="选择要导出的对象范围",
        items=[
            ('ALL', "所有对象", "导出场景中的所有可见对象"),
            ('SELECTED', "选中对象", "只导出当前选中的对象"),
            ('VISIBLE', "可见对象", "导出当前可见的对象（非隐藏）"),
        ],
        default='ALL'
    )
    
    # 对象类型过滤
    export_mesh: BoolProperty(
        name="网格",
        description="导出网格对象",
        default=True
    )
    
    export_armature: BoolProperty(
        name="骨架",
        description="导出骨架对象",
        default=True
    )
    
    export_curve: BoolProperty(
        name="曲线",
        description="导出曲线对象",
        default=False
    )
    
    export_surface: BoolProperty(
        name="曲面",
        description="导出曲面对象",
        default=False
    )
    
    export_empty: BoolProperty(
        name="空对象",
        description="导出空对象（用于层级结构）",
        default=False
    )
    
    # 导出选项
    apply_modifiers: BoolProperty(
        name="应用修改器",
        description="导出时应用对象的修改器",
        default=True
    )
    
    export_animations: BoolProperty(
        name="导出动画",
        description="导出动画数据",
        default=True
    )
    
    # 骨架导出设置
    armature_primary_bone_axis: EnumProperty(
        name="主骨骼轴",
        description="骨骼的主要轴向",
        items=[
            ('X', "X 轴", "使用X轴作为主轴"),
            ('Y', "Y 轴", "使用Y轴作为主轴"),
            ('-X', "-X 轴", "使用负X轴作为主轴"),
            ('-Y', "-Y 轴", "使用负Y轴作为主轴"),
        ],
        default='Y'
    )
    
    armature_secondary_bone_axis: EnumProperty(
        name="次骨骼轴",
        description="骨骼的次要轴向",
        items=[
            ('X', "X 轴", "使用X轴作为次轴"),
            ('Y', "Y 轴", "使用Y轴作为次轴"),
            ('Z', "Z 轴", "使用Z轴作为次轴"),
            ('-X', "-X 轴", "使用负X轴作为次轴"),
            ('-Y', "-Y 轴", "使用负Y轴作为次轴"),
            ('-Z', "-Z 轴", "使用负Z轴作为次轴"),
        ],
        default='X'
    )
    
    armature_fbx_node_type: EnumProperty(
        name="骨架FBX节点类型",
        description="FBX文件中骨架节点的类型",
        items=[
            ('NULL', "Null", "使用Null节点类型"),
            ('ROOT', "Root", "使用Root节点类型"),
            ('LIMBNODE', "LimbNode", "使用LimbNode节点类型"),
        ],
        default='NULL'
    )
    
    armature_only_deform_bones: BoolProperty(
        name="仅变形骨骼",
        description="只导出用于变形的骨骼",
        default=False
    )
    
    armature_add_leaf_bones: BoolProperty(
        name="添加叶骨骼",
        description="为骨骼链末端添加叶骨骼",
        default=False
    )
    
    # 动画导出详细设置
    anim_key_all_bones: BoolProperty(
        name="关键帧所有骨骼",
        description="为骨架中的所有骨骼导出关键帧",
        default=True
    )
    
    anim_nla_strips: BoolProperty(
        name="NLA 条带",
        description="导出NLA编辑器中的动画条带",
        default=False
    )
    
    anim_all_actions: BoolProperty(
        name="所有动作",
        description="导出场景中的所有动作",
        default=False
    )
    
    anim_force_start_end_keying: BoolProperty(
        name="强制起始/结束关键帧",
        description="在动画开始和结束时强制添加关键帧",
        default=True
    )
    
    anim_sampling_rate: FloatProperty(
        name="采样率",
        description="动画采样率（每秒帧数的倍数）",
        default=1.0,
        min=0.01,
        max=100.0,
        step=0.1
    )
    
    anim_simplify_factor: FloatProperty(
        name="简化",
        description="关键帧简化因子（0=无简化，1=最大简化）",
        default=1.0,
        min=0.0,
        max=1.0,
        step=0.1
    )
    
    global_scale: FloatProperty(
        name="全局缩放",
        description="导出时的全局缩放系数",
        default=1.0,
        min=0.001,
        max=1000.0,
        step=0.1
    )
    
    # UI显示控制
    show_export_settings: BoolProperty(
        name="显示导出设置",
        description="显示详细的导出设置面板",
        default=False
    )


# 属性类列表
classes = [
    BlenderToMaxSettings,
]


def register():
    """注册属性"""
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # 将属性组添加到场景中
    bpy.types.Scene.blender_to_max_settings = bpy.props.PointerProperty(
        type=BlenderToMaxSettings
    )


def unregister():
    """注销属性"""
    # 删除场景属性
    if hasattr(bpy.types.Scene, 'blender_to_max_settings'):
        del bpy.types.Scene.blender_to_max_settings
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)