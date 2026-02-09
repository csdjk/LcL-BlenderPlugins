"""
Model Inspector User Interface
模型检测器用户界面
"""

import bpy
from bpy.types import Panel
from . import mesh_helpers
import math


class VIEW3D_PT_ModelInspectorMain(Panel):
    """模型检测器主面板"""
    bl_label = "🔍 模型检测工具"
    bl_idname = "VIEW3D_PT_model_inspector_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "LcL"
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.model_inspector
        
        # 获取统计数据
        stats = mesh_helpers.get_inspection_stats()
        
        # 检测功能开关区域 - 参考check_toolbox布局
        box = layout.box()
        box.label(text="检测功能", icon='SETTINGS')
        
        # 相交检测行
        row = box.row()
        col = row.column()
        col.prop(props, "check_intersection", text="相交检测")
        
        col2 = row.column_flow(columns=3)
        col2.enabled = props.check_intersection
        col2.prop(props, "intersect_face_color", text="")
        if stats['intersect_faces'] > 0:
            col2.label(text=f"{stats['intersect_faces']}", icon='ERROR')
        else:
            col2.label(text="0")
        # 占位符
        col2.label(text="")
        
        # 相交检测子选项
        if props.check_intersection:
            sub_row = box.row()
            sub_row.enabled = props.check_intersection
            sub_row.prop(props, "intersect_type", text="类型")
            sub_row.prop(props, "intersect_threshold", text="阈值")
        
        # 扭曲检测行
        row = box.row()
        col = row.column()
        col.prop(props, "check_distortion", text="扭曲检测")
        
        col2 = row.column_flow(columns=3)
        col2.enabled = props.check_distortion
        col2.prop(props, "distortion_face_color", text="")
        if stats['distorted_faces'] > 0:
            col2.label(text=f"{stats['distorted_faces']}", icon='MOD_TRIANGULATE')
        else:
            col2.label(text="0")
        # 占位符
        col2.label(text="")
        
        # 扭曲角度设置
        if props.check_distortion:
            sub_row = box.row()
            sub_row.enabled = props.check_distortion
            sub_row.prop(props, "distortion_angle", text="扭曲角度")
        
        # 检测操作按钮和自动更新
        layout.separator(factor=0.5)
        box = layout.box()
        col = box.column(align=True)
        
        # 自动更新和检测按钮同一行
        row = col.row(align=True)
        row.prop(props, "auto_update", text="自动更新")
        
        # 当自动更新关闭时显示检测按钮
        if not props.auto_update:
            # 根据开启的功能显示相应按钮
            if props.check_intersection and props.check_distortion:
                # 两个功能都开启
                row.scale_y = 1.4
                row.operator("mesh.model_inspector_check_all", 
                            text="检测", icon='NONE')
            
            elif props.check_intersection:
                # 仅相交检测
                row.scale_y = 1.4
                if props.intersect_type == 'SELF':
                    row.operator("mesh.model_inspector_check_self", 
                               text="检测", icon='NONE')
                elif props.intersect_type == 'OBJECTS':
                    row.operator("mesh.model_inspector_check_objects", 
                               text="检测", icon='NONE')
                else:  # BOTH
                    row.operator("mesh.model_inspector_check_all", 
                               text="检测", icon='NONE')
            
            elif props.check_distortion:
                # 仅扭曲检测
                row.scale_y = 1.4
                row.operator("mesh.model_inspector_check_distortion", 
                            text="检测", icon='NONE')
            
            else:
                # 都未开启
                row.enabled = False
                row.label(text="请选择至少一种检测功能", icon='INFO')
        else:
            # 自动更新开启时的提示
            info_row = col.row()
            info_row.label(text="自动更新已启用，检测将在每帧自动执行", icon='TIME')
        
        # 当前检测对象显示
        if stats['objects_count'] > 0:
            layout.separator(factor=0.3)
            object_name = mesh_helpers.get_display_object_name(context)
            info_row = layout.row()
            info_row.label(text=f"检测对象: {object_name}", icon='OBJECT_DATA')
        
        # 选择问题面片（仅在编辑模式下显示）
        if context.mode == 'EDIT_MESH' and stats['objects_count'] > 0:
            layout.separator()
            box = layout.box()
            col = box.column()
            col.operator("mesh.model_inspector_select_faces", 
                        text="选择问题面片", icon='RESTRICT_SELECT_OFF')
        


class VIEW3D_PT_ModelInspectorResults(Panel):
    """模型检测器结果面板"""
    bl_label = "检测信息"
    bl_idname = "VIEW3D_PT_model_inspector_results"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "LcL"
    bl_parent_id = "VIEW3D_PT_model_inspector_main"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.model_inspector
        
        # 详细统计信息
        stats = mesh_helpers.get_inspection_stats()
        
        if stats['objects_count'] > 0:
            layout.separator()
            box = layout.box()
            box.label(text="详细统计:", icon='LINENUMBERS_ON')
            
            col = box.column()
            col.label(text=f"• 涉及对象: {stats['objects_count']}")
            col.label(text=f"• 总问题面: {stats['faces_count']}")
            
            if stats['intersect_faces'] > 0:
                col.label(text=f"• 相交面: {stats['intersect_faces']}")
            if stats['distorted_faces'] > 0:
                col.label(text=f"• 扭曲面: {stats['distorted_faces']}")
            
            # 按对象显示详细信息
            inspection_objects = {}
            for data in mesh_helpers._inspection_data:
                obj_name = data['object'].name if data['object'] else "未知"
                face_count = len(data['faces'])
                inspect_type = data.get('inspection_type', 'INTERSECT')
                
                if obj_name not in inspection_objects:
                    inspection_objects[obj_name] = {'INTERSECT': 0, 'DISTORTION': 0}
                inspection_objects[obj_name][inspect_type] += face_count
            
            if inspection_objects:
                col.separator()
                col.label(text="按对象分类:")
                for obj_name, counts in inspection_objects.items():
                    info_parts = []
                    if counts['INTERSECT'] > 0:
                        info_parts.append(f"相交{counts['INTERSECT']}")
                    if counts['DISTORTION'] > 0:
                        info_parts.append(f"扭曲{counts['DISTORTION']}")
                    
                    if info_parts:
                        info_text = f"• {obj_name}: {', '.join(info_parts)}"
                        col.label(text=info_text, icon='OBJECT_DATA')


# 面板类列表
classes = [
    VIEW3D_PT_ModelInspectorMain,
    VIEW3D_PT_ModelInspectorResults,
]


def register():
    """注册面板"""
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    """注销面板"""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)