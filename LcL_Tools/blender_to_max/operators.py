"""
BlenderToMax同步操作符
"""

import bpy
from bpy.types import Operator
import os
import tempfile
from . import sync_utils

# FBX导入相关常量
SYNCBLENDER_EXCHANGE_FOLDER = "SyncBlender_Exchange"
FBX_FILENAME = "export_model.fbx"


class IMPORT_OT_SyncBlender_ImportFBX(Operator):
    """从SyncBlender交换目录导入FBX模型"""
    bl_idname = "import_scene.syncblender_import_fbx"
    bl_label = "导入SyncBlender FBX"
    bl_description = "从Max导出的FBX模型文件导入到Blender"
    bl_options = {'REGISTER', 'UNDO'}
    
    def get_fbx_file_path(self):
        """构建FBX文件路径"""
        return sync_utils.get_fbx_import_path()
    
    def execute(self, context):
        fbx_file_path = self.get_fbx_file_path()
        
        # Check if file exists
        if not os.path.exists(fbx_file_path):
            self.report({'ERROR'}, f"FBX file not found: {fbx_file_path}")
            return {'CANCELLED'}
        
        # Get objects before import
        objects_before = set(bpy.data.objects)
        
        # Import FBX file with error handling
        try:
            bpy.ops.import_scene.fbx(filepath=fbx_file_path)
        except RuntimeError as e:
            error_msg = str(e)
            # 检查是否是 ASCII FBX 不支持的错误
            if "ASCII FBX" in error_msg or "ASCII FBX文件不被支持" in error_msg:
                # 显示友好的错误提示
                def draw_message(self, context):
                    layout = self.layout
                    layout.label(text="不支持导入 ASCII 格式的 FBX 文件")
                    layout.label(text="请确保从 3ds Max 导出时选择二进制格式")
                    layout.separator()
                    layout.label(text="导出设置建议:")
                    layout.label(text="• 文件格式: FBX Binary")
                    layout.label(text="• 版本: 2020 或更高")
                
                bpy.context.window_manager.popup_menu(draw_message, title="FBX 导入错误", icon='ERROR')
                self.report({'ERROR'}, "不支持 ASCII 格式的 FBX 文件")
                return {'CANCELLED'}
            else:
                # 其他 FBX 导入错误
                self.report({'ERROR'}, f"FBX 导入失败: {error_msg}")
                return {'CANCELLED'}
        
        # Get newly imported objects
        objects_after = set(bpy.data.objects)
        imported_objects = objects_after - objects_before
        
        if imported_objects:
            # Select newly imported objects
            bpy.ops.object.select_all(action='DESELECT')
            for obj in imported_objects:
                obj.select_set(True)
                if obj.type == 'MESH':
                    context.view_layer.objects.active = obj
            
            self.report({'INFO'}, f"Successfully imported FBX model with {len(imported_objects)} objects")
            print(f"SyncBlender: Imported {len(imported_objects)} objects from {fbx_file_path}")
            
            # Print imported object names
            for obj in imported_objects:
                print(f"  - {obj.name} ({obj.type})")
            
        else:
            self.report({'WARNING'}, "FBX file imported but no new objects detected")
        
        return {'FINISHED'}


class EXPORT_OT_SyncBlender_ExportFBX(Operator):
    """导出对象到SyncBlender交换目录"""
    bl_idname = "export_scene.syncblender_export_fbx"
    bl_label = "导出SyncBlender FBX"
    bl_description = "将对象导出为FBX文件到Max交换目录"
    bl_options = {'REGISTER', 'UNDO'}
    
    def get_export_file_path(self):
        """构建导出FBX文件路径"""
        return sync_utils.get_fbx_import_path()  # 使用相同路径
    
    def get_exportable_objects(self, context, settings):
        """根据设置获取要导出的对象列表"""
        # 构建允许的对象类型列表
        allowed_types = set()
        if settings.export_mesh:
            allowed_types.add('MESH')
        if settings.export_armature:
            allowed_types.add('ARMATURE')
        if settings.export_curve:
            allowed_types.add('CURVE')
        if settings.export_surface:
            allowed_types.add('SURFACE')
        if settings.export_empty:
            allowed_types.add('EMPTY')
        
        # 根据导出范围获取对象
        if settings.export_scope == 'ALL':
            # 导出所有对象（排除隐藏的）
            candidate_objects = [obj for obj in context.scene.objects if obj.visible_get()]
        elif settings.export_scope == 'SELECTED':
            # 只导出选中的对象
            candidate_objects = list(context.selected_objects)
        elif settings.export_scope == 'VISIBLE':
            # 导出可见对象
            candidate_objects = [obj for obj in context.scene.objects if obj.visible_get()]
        else:
            candidate_objects = []
        
        # 按类型过滤
        exportable_objects = [obj for obj in candidate_objects if obj.type in allowed_types]
        
        return exportable_objects
    
    @classmethod
    def poll(cls, context):
        """检查是否有场景对象"""
        return len(context.scene.objects) > 0
    
    def execute(self, context):
        settings = context.scene.blender_to_max_settings
        
        # 获取要导出的对象
        exportable_objects = self.get_exportable_objects(context, settings)
        
        if not exportable_objects:
            if settings.export_scope == 'SELECTED':
                self.report({'ERROR'}, "No selected exportable objects")
            else:
                self.report({'ERROR'}, "No exportable objects in scene")
            return {'CANCELLED'}
        
        fbx_export_path = self.get_export_file_path()
        
        # Ensure export directory exists
        export_dir = os.path.dirname(fbx_export_path)
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
            print(f"SyncBlender: Created exchange directory {export_dir}")
        
        # 根据导出范围选择对象
        if settings.export_scope != 'ALL':
            # 首先清除所有选择
            bpy.ops.object.select_all(action='DESELECT')
            # 选择要导出的对象
            for obj in exportable_objects:
                obj.select_set(True)
            use_selection = True
        else:
            # 导出所有对象时不使用选择
            use_selection = False
        
        # 构建对象类型集合
        object_types = set()
        if settings.export_mesh:
            object_types.add('MESH')
        if settings.export_armature:
            object_types.add('ARMATURE')
        if settings.export_curve:
            object_types.add('OTHER')  # 曲线归类为OTHER
        if settings.export_surface:
            object_types.add('OTHER')  # 曲面归类为OTHER
        if settings.export_empty:
            object_types.add('EMPTY')
        
        # Export objects to FBX
        bpy.ops.export_scene.fbx(
            filepath=fbx_export_path,
            use_selection=use_selection,
            use_active_collection=False,
            global_scale=settings.global_scale,
            apply_unit_scale=True,
            apply_scale_options='FBX_SCALE_NONE',
            use_space_transform=True,
            bake_space_transform=False,
            object_types=object_types,
            use_mesh_modifiers=settings.apply_modifiers,
            use_mesh_modifiers_render=settings.apply_modifiers,
            mesh_smooth_type='OFF',
            use_subsurf=False,
            use_mesh_edges=False,
            use_tspace=False,
            use_triangles=False,
            use_custom_props=False,
            add_leaf_bones=settings.armature_add_leaf_bones,
            primary_bone_axis=settings.armature_primary_bone_axis,
            secondary_bone_axis=settings.armature_secondary_bone_axis,
            use_armature_deform_only=settings.armature_only_deform_bones,
            armature_nodetype=settings.armature_fbx_node_type,
            bake_anim=settings.export_animations,
            bake_anim_use_all_bones=settings.anim_key_all_bones if settings.export_animations else False,
            bake_anim_use_nla_strips=settings.anim_nla_strips if settings.export_animations else False,
            bake_anim_use_all_actions=settings.anim_all_actions if settings.export_animations else False,
            bake_anim_force_startend_keying=settings.anim_force_start_end_keying if settings.export_animations else False,
            bake_anim_step=settings.anim_sampling_rate if settings.export_animations else 1.0,
            bake_anim_simplify_factor=settings.anim_simplify_factor if settings.export_animations else 1.0,
            path_mode='AUTO',
            embed_textures=False,
            batch_mode='OFF',
            use_batch_own_dir=True,
            use_metadata=True
        )
        
        # Check if file was created successfully
        if os.path.exists(fbx_export_path):
            file_size = os.path.getsize(fbx_export_path)
            if file_size > 0:
                size_mb = file_size / (1024 * 1024)
                if size_mb >= 1:
                    size_text = f"{size_mb:.1f} MB"
                else:
                    size_kb = file_size / 1024
                    size_text = f"{size_kb:.1f} KB"
                
                self.report({'INFO'}, f"Successfully exported {len(exportable_objects)} objects to FBX file ({size_text})")
                print(f"SyncBlender: Exported {len(exportable_objects)} objects to {fbx_export_path}")
                
                # Print exported object names
                for obj in exportable_objects:
                    print(f"  - {obj.name} ({obj.type})")
                
                # 显示成功弹窗 - 使用更安全的popup_menu方式
                def draw_success_message(popup_self, context):
                    layout = popup_self.layout
                    
                    # 显示导出的对象列表（最多显示5个）
                    if len(exportable_objects) <= 5:
                        # 多个对象时，文件大小单独一行
                        layout.label(text="导出对象:")
                        for obj in exportable_objects:
                            layout.label(text=f"• {obj.name}", icon='OBJECT_DATA')
                        layout.separator()
                        layout.label(text=f"文件大小: {size_text}")
                    elif len(exportable_objects) > 5:
                        layout.label(text="导出对象:")
                        for obj in exportable_objects[:3]:
                            layout.label(text=f"• {obj.name}", icon='OBJECT_DATA')
                        layout.label(text=f"... 及其他 {len(exportable_objects)-3} 个对象", icon='THREE_DOTS')
                        layout.separator()
                        layout.label(text=f"文件大小: {size_text}")
                
                # 使用window_manager的popup_menu，这种方式更稳定
                context.window_manager.popup_menu(draw_success_message, title="已发送到Max", icon='CHECKMARK')
            else:
                self.report({'WARNING'}, "Exported FBX file is empty")
                return {'CANCELLED'}
        else:
            self.report({'ERROR'}, "FBX export failed, file not created")
            return {'CANCELLED'}
        
        return {'FINISHED'}


# 算子类列表
classes = [
    IMPORT_OT_SyncBlender_ImportFBX,
    EXPORT_OT_SyncBlender_ExportFBX,
]


def register():
    """注册操作符"""
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    """注销操作符"""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)