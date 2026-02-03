"""
相交检测器用户界面
"""

import bpy
from bpy.types import Panel
from ..core import mesh_helpers


class VIEW3D_PT_IntersectionDetectorMain(Panel):
    """相交检测器主面板"""
    bl_label = "🔍 相交检测器"
    bl_idname = "VIEW3D_PT_intersection_detector_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "相交检测"
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.intersection_detector
        
        # 检测操作区域
        box = layout.box()
        col = box.column(align=True)
        
        # 检测类型选择
        row = col.row(align=True)
        row.prop(props, "detection_type", text="")
        
        # 检测按钮单独一排
        col.separator(factor=0.5)
        row = col.row(align=True)
        row.scale_y = 1.5  # 让按钮更高
        
        if props.detection_type == 'SELF':
            row.operator("mesh.intersection_detector_check_self", 
                        text="🔍 自相交检测", icon='NONE')
        elif props.detection_type == 'OBJECTS':
            row.operator("mesh.intersection_detector_check_objects", 
                        text="🔍 对象间相交检测", icon='NONE')
        else:  # BOTH
            row.operator("mesh.intersection_detector_check_all", 
                        text="🔍 全面相交检测", icon='NONE')
        
        # 状态和控制区域
        layout.separator(factor=0.5)
        box = layout.box()
        col = box.column()
        
        # 统计信息 - 紧凑显示
        stats = mesh_helpers.get_intersection_stats()
        row = col.row()
        row.label(text=f"对象: {stats['objects_count']}", icon='OBJECT_DATA')
        row.label(text=f"面数: {stats['faces_count']}", icon='FACE_MAPS')
        
        # 控制按钮 - 水平排列
        col.separator(factor=0.3)
        row = col.row(align=True)
        
        # 颜色显示按钮
        color_btn = row.row(align=True)
        if props.show_color_display and stats['objects_count'] > 0:
            # 激活状态 - 高亮显示
            color_btn.operator_context = 'INVOKE_DEFAULT'
            color_btn.prop(props, "show_color_display", text="颜色显示", icon='OUTLINER_OB_LIGHT', toggle=True)
        elif props.show_color_display:
            # 开启但无数据
            color_btn.prop(props, "show_color_display", text="颜色显示", icon='LIGHT_SUN', toggle=True)
        else:
            # 关闭状态
            color_btn.prop(props, "show_color_display", text="颜色显示", icon='LIGHT', toggle=True)
        
        # 自动更新按钮
        auto_btn = row.row(align=True)
        if props.auto_update:
            # 开启状态 - 高亮显示
            auto_btn.operator_context = 'INVOKE_DEFAULT'
            auto_btn.prop(props, "auto_update", text="自动更新", icon='PLAY', toggle=True)
        else:
            # 关闭状态
            auto_btn.prop(props, "auto_update", text="自动更新", icon='PAUSE', toggle=True)
        
        # 操作按钮 - 水平排列
        col.separator(factor=0.3)
        row = col.row(align=True)
        row.operator("mesh.intersection_detector_select_intersected", 
                    text="选择面", icon='RESTRICT_SELECT_OFF')
        row.operator("mesh.intersection_detector_clear_data", 
                    text="清空", icon='TRASH')


class VIEW3D_PT_IntersectionDetectorSettings(Panel):
    """相交检测器设置面板"""
    bl_label = "设置"
    bl_idname = "VIEW3D_PT_intersection_detector_settings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "相交检测"
    bl_parent_id = "VIEW3D_PT_intersection_detector_main"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.intersection_detector
        
        # 颜色配置
        box = layout.box()
        box.label(text="颜色配置:", icon='COLORSET_01_VEC')
        col = box.column()
        col.prop(props, "intersect_face_color", text="面颜色")
        col.prop(props, "intersect_edge_color", text="边颜色")
        
        # 检测参数
        layout.separator()
        box = layout.box()
        box.label(text="检测参数:", icon='PREFERENCES')
        col = box.column()
        col.prop(props, "intersect_threshold", text="阈值")


class VIEW3D_PT_IntersectionDetectorResults(Panel):
    """相交检测器结果面板"""
    bl_label = "检测结果"
    bl_idname = "VIEW3D_PT_intersection_detector_results"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "相交检测"
    bl_parent_id = "VIEW3D_PT_intersection_detector_main"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.intersection_detector
        
        # 最后检测结果
        box = layout.box()
        box.label(text="最后检测:", icon='INFO')
        col = box.column()
        col.label(text=props.last_check_results, icon='NONE')
        
        # 详细统计信息
        stats = mesh_helpers.get_intersection_stats()
        
        if stats['objects_count'] > 0 or stats['faces_count'] > 0:
            layout.separator()
            box = layout.box()
            box.label(text="详细统计:", icon='LINENUMBERS_ON')
            
            col = box.column()
            col.label(text=f"• 涉及对象数: {stats['objects_count']}")
            col.label(text=f"• 相交面总数: {stats['faces_count']}")
            
            # 按对象显示详细信息
            intersection_objects = {}
            for data in mesh_helpers._intersection_data:
                obj_name = data['object'].name if data['object'] else "未知"
                face_count = len(data['faces'])
                intersect_type = data['type']
                
                if obj_name not in intersection_objects:
                    intersection_objects[obj_name] = {'SELF': 0, 'BETWEEN': 0}
                intersection_objects[obj_name][intersect_type] += face_count
            
            if intersection_objects:
                col.separator()
                col.label(text="按对象分类:")
                for obj_name, counts in intersection_objects.items():
                    info_text = f"• {obj_name}:"
                    details = []
                    if counts['SELF'] > 0:
                        details.append(f"自相交 {counts['SELF']}")
                    if counts['BETWEEN'] > 0:
                        details.append(f"对象间 {counts['BETWEEN']}")
                    if details:
                        info_text += " " + ", ".join(details)
                    col.label(text=info_text, icon='OBJECT_DATA')


# 面板类列表
classes = [
    VIEW3D_PT_IntersectionDetectorMain,
    VIEW3D_PT_IntersectionDetectorSettings,
    VIEW3D_PT_IntersectionDetectorResults,
]


def register():
    """注册面板"""
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    """注销面板"""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)