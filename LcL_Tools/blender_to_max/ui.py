"""
BlenderToMax同步用户界面
"""

import bpy
from bpy.types import Panel
from . import sync_utils


class VIEW3D_PT_BlenderToMaxMain(Panel):
    """BlenderToMax主面板"""
    bl_label = "🔄 BlenderToMax"
    bl_idname = "VIEW3D_PT_blender_to_max_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "LcL"
    
    def draw(self, context):
        layout = self.layout
        
        # 导入区域
        box = layout.box()
        col = box.column(align=True)
        
        # 检查FBX文件状态
        file_info = sync_utils.get_fbx_file_info()
        
        # 导入按钮
        import_btn = col.row()
        import_btn.scale_y = 1.5
        import_btn.operator("import_scene.syncblender_import_fbx", 
                          text="Max To Blender", icon='IMPORT')
        
        # 文件状态信息（紧凑显示）
        if file_info['exists']:
            info_row = col.row(align=True)
            info_row.scale_y = 0.8
            info_row.label(text="FBX Ready", icon='CHECKMARK')
            
            if file_info['size'] > 0:
                size_mb = file_info['size'] / (1024 * 1024)
                if size_mb >= 1:
                    size_text = f"{size_mb:.1f}MB"
                else:
                    size_kb = file_info['size'] / 1024
                    size_text = f"{size_kb:.1f}KB"
                info_row.label(text=size_text)
        else:
            info_row = col.row(align=True)
            info_row.scale_y = 0.8
            info_row.label(text="No FBX file found", icon='ERROR')
        
        # 导出区域
        box = layout.box()
        col = box.column(align=True)
        
        # 获取设置
        settings = context.scene.blender_to_max_settings
        
        # 导出范围和设置按钮
        row = col.row(align=True)
        row.prop(settings, "export_scope", text="")
        settings_btn = row.row()
        settings_btn.scale_x = 0.7
        settings_btn.prop(settings, "show_export_settings", 
                         icon='SETTINGS' if not settings.show_export_settings else 'DOWNARROW_HLT',
                         text="", toggle=True)
        
        # 导出按钮
        export_btn = col.row()
        export_btn.scale_y = 1.5
        export_btn.operator("export_scene.syncblender_export_fbx", 
                          text="Blender To Max", icon='EXPORT')
        
        # 导出状态信息（紧凑显示在按钮下方）
        info_row = col.row(align=True)
        info_row.scale_y = 0.8
        
        if settings.export_scope == 'ALL':
            all_objects = [obj for obj in context.scene.objects if obj.visible_get()]
            exportable_count = len([obj for obj in all_objects 
                                  if (obj.type == 'MESH' and settings.export_mesh) or
                                     (obj.type == 'ARMATURE' and settings.export_armature) or
                                     (obj.type == 'CURVE' and settings.export_curve) or
                                     (obj.type == 'SURFACE' and settings.export_surface) or
                                     (obj.type == 'EMPTY' and settings.export_empty)])
            
            if exportable_count > 0:
                info_row.label(text=f"{exportable_count} objects", icon='CHECKMARK')
            else:
                info_row.label(text="No exportable objects", icon='ERROR')
                
        elif settings.export_scope == 'SELECTED':
            selected_objects = [obj for obj in context.selected_objects
                              if (obj.type == 'MESH' and settings.export_mesh) or
                                 (obj.type == 'ARMATURE' and settings.export_armature) or
                                 (obj.type == 'CURVE' and settings.export_curve) or
                                 (obj.type == 'SURFACE' and settings.export_surface) or
                                 (obj.type == 'EMPTY' and settings.export_empty)]
            
            if selected_objects:
                if len(selected_objects) == 1:
                    info_row.label(text=f"Selected: {selected_objects[0].name}", icon='CHECKMARK')
                else:
                    info_row.label(text=f"{len(selected_objects)} selected", icon='CHECKMARK')
            else:
                info_row.label(text="No selected objects", icon='ERROR')
                
        elif settings.export_scope == 'VISIBLE':
            visible_objects = [obj for obj in context.scene.objects if obj.visible_get()]
            exportable_count = len([obj for obj in visible_objects
                                  if (obj.type == 'MESH' and settings.export_mesh) or
                                     (obj.type == 'ARMATURE' and settings.export_armature) or
                                     (obj.type == 'CURVE' and settings.export_curve) or
                                     (obj.type == 'SURFACE' and settings.export_surface) or
                                     (obj.type == 'EMPTY' and settings.export_empty)])
            
            if exportable_count > 0:
                info_row.label(text=f"{exportable_count} visible", icon='CHECKMARK')
            else:
                info_row.label(text="No visible objects", icon='ERROR')
        
        # 详细导出设置
        if settings.show_export_settings:
            col.separator()
            
            # 对象类型过滤
            sub_box = col.box()
            sub_box.label(text="对象类型:", icon='OBJECT_DATAMODE')
            type_col = sub_box.column(align=True)
            
            row1 = type_col.row(align=True)
            row1.prop(settings, "export_mesh", text="网格")
            row1.prop(settings, "export_animations", text="动画")
            
            row2 = type_col.row(align=True)
            row2.prop(settings, "export_armature", text="骨架")
            row2.prop(settings, "export_curve", text="曲线")
            
            row3 = type_col.row(align=True)
            row3.prop(settings, "export_surface", text="曲面")
            row3.prop(settings, "export_empty", text="空对象")
            
            # 导出选项
            sub_box = col.box()
            sub_box.label(text="导出选项:", icon='MODIFIER')
            option_col = sub_box.column(align=True)
            
            option_col.prop(settings, "apply_modifiers", text="应用修改器")
            option_col.prop(settings, "global_scale", text="全局缩放")
            
            # 骨架导出设置
            if settings.export_armature:
                sub_box = col.box()
                sub_box.label(text="骨架", icon='ARMATURE_DATA')
                armature_col = sub_box.column(align=True)
                
                # 骨骼轴向设置
                axis_row = armature_col.row(align=True)
                axis_row.prop(settings, "armature_primary_bone_axis", text="主轴")
                axis_row.prop(settings, "armature_secondary_bone_axis", text="次轴")
                
                # 骨架选项
                armature_col.prop(settings, "armature_fbx_node_type", text="FBX节点类型")
                armature_col.prop(settings, "armature_only_deform_bones", text="仅变形骨骼")
                armature_col.prop(settings, "armature_add_leaf_bones", text="添加叶骨骼")
            
            # 动画导出详细设置
            if settings.export_animations:
                sub_box = col.box()
                sub_box.label(text="动画", icon='ANIM')
                anim_col = sub_box.column(align=True)
                
                # 动画导出详细选项
                anim_col.prop(settings, "anim_key_all_bones", text="关键帧所有骨骼")
                anim_col.prop(settings, "anim_nla_strips", text="NLA 条带")
                anim_col.prop(settings, "anim_all_actions", text="所有动作")
                anim_col.prop(settings, "anim_force_start_end_keying", text="强制起始/结束关键帧")
                
                # 采样和简化设置
                anim_col.separator(factor=0.5)
                anim_col.prop(settings, "anim_sampling_rate", text="采样率")
                anim_col.prop(settings, "anim_simplify_factor", text="简化")


class VIEW3D_PT_BlenderToMaxSettings(Panel):
    """BlenderToMax设置面板"""
    bl_label = "设置"
    bl_idname = "VIEW3D_PT_blender_to_max_settings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "LcL"
    bl_parent_id = "VIEW3D_PT_blender_to_max_main"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        
        # 路径信息
        box = layout.box()
        box.label(text="交换目录信息:", icon='FOLDER_REDIRECT')
        
        col = box.column()
        
        # 交换目录路径
        exchange_path = sync_utils.get_syncblender_exchange_path()
        path_parts = exchange_path.split('\\')
        if len(path_parts) > 2:
            display_exchange = "...\\" + "\\".join(path_parts[-2:])
        else:
            display_exchange = exchange_path
        col.label(text=f"交换目录:", icon='NONE')
        col.label(text=display_exchange, icon='NONE')
        
        # FBX文件路径
        fbx_path = sync_utils.get_fbx_import_path()
        path_parts = fbx_path.split('\\')
        if len(path_parts) > 3:
            display_fbx = "...\\" + "\\".join(path_parts[-2:])
        else:
            display_fbx = fbx_path
        col.separator(factor=0.5)
        col.label(text=f"FBX文件:", icon='NONE')
        col.label(text=display_fbx, icon='NONE')
        
        # 刷新按钮
        layout.separator()
        row = layout.row()
        row.operator("wm.redraw_timer", text="刷新状态", icon='FILE_REFRESH')


# 面板类列表
classes = [
    VIEW3D_PT_BlenderToMaxMain,
    # VIEW3D_PT_BlenderToMaxSettings,  # 隐藏设置面板
]


def register():
    """注册面板"""
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    """注销面板"""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)