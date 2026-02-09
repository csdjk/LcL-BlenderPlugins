"""
模型检测器操作符
从 check_toolbox 移植并优化的模型检测操作
包含相交检测和扭曲检测功能
"""

import bpy
from bpy.types import Operator
from bpy.props import EnumProperty
import bmesh
from . import mesh_helpers


def update_last_inspected_objects(context, objects):
    """更新最后检测的对象名称列表"""
    props = context.scene.model_inspector
    if not objects:
        return
    
    # 获取对象名称列表
    object_names = [obj.name for obj in objects if obj and obj.type == 'MESH']
    
    if len(object_names) == 1:
        display_name = object_names[0]
    elif len(object_names) > 1:
        display_name = f"{object_names[0]} 等{len(object_names)}个对象"
    else:
        display_name = ""
    
    props.last_inspected_objects = display_name


def get_objects_for_inspection(context):
    """智能获取要检测的对象，优先使用当前选中对象，否则使用最后检测的对象"""
    # 首先尝试获取当前选中的mesh对象
    selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
    if selected_objects:
        return selected_objects
    
    # 如果没有选中对象，尝试根据最后检测的对象名称找到对象
    if hasattr(context.scene, 'model_inspector'):
        last_objects_name = context.scene.model_inspector.last_inspected_objects
        if last_objects_name:
            # 解析对象名称（可能是单个对象名或"对象名 等N个对象"格式）
            if " 等" in last_objects_name:
                # 多对象格式，只取第一个对象名
                first_name = last_objects_name.split(" 等")[0]
            else:
                # 单对象格式
                first_name = last_objects_name
            
            # 在场景中查找对象
            if first_name in context.scene.objects:
                obj = context.scene.objects[first_name]
                if obj.type == 'MESH':
                    return [obj]
    
    return []


class MESH_OT_ModelInspector_CheckSelfIntersect(Operator):
    """检查自相交"""
    bl_idname = "mesh.model_inspector_check_self"
    bl_label = "检查自相交"
    bl_description = "检测当前对象的自相交面"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.model_inspector
        
        # 智能获取检测对象
        inspection_objects = get_objects_for_inspection(context)
        if not inspection_objects:
            self.report({'ERROR'}, "请选择一个网格对象或确保之前检测过的对象仍存在于场景中")
            return {'CANCELLED'}
        
        # 自相交检测只处理第一个对象
        obj = inspection_objects[0]
        
        # 清空之前的数据
        mesh_helpers.clear_inspection_data()
        
        # 执行自相交检测
        faces_intersect = mesh_helpers.bmesh_check_self_intersect_object(
            obj, threshold=props.intersect_threshold
        )
        
        # 更新检测对象记录
        update_last_inspected_objects(context, [obj])
        
        if len(faces_intersect) > 0:
            # 添加到显示数据
            mesh_helpers.add_inspection_data(obj, faces_intersect, "INTERSECT")
            
            # 自动启用显示
            mesh_helpers.enable_display()
            
            result_msg = f"发现 {len(faces_intersect)} 个自相交面"
            props.last_check_results = result_msg
        else:
            props.last_check_results = "未发现自相交"
        
        return {'FINISHED'}


class MESH_OT_ModelInspector_CheckDistortion(Operator):
    """检查扭曲面片"""
    bl_idname = "mesh.model_inspector_check_distortion"
    bl_label = "检查扭曲"
    bl_description = "检测网格中的扭曲面片（非平面）"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.model_inspector
        
        # 智能获取检测对象
        inspection_objects = get_objects_for_inspection(context)
        if not inspection_objects:
            self.report({'ERROR'}, "请选择一个网格对象或确保之前检测过的对象仍存在于场景中")
            return {'CANCELLED'}
        
        # 扭曲检测只处理第一个对象
        obj = inspection_objects[0]
        
        # 清空之前的数据
        mesh_helpers.clear_inspection_data()
        
        # 执行扭曲检测
        faces_distorted = mesh_helpers.check_distorted_faces(
            obj, angle_threshold=props.distortion_angle
        )
        
        # 更新检测对象记录
        update_last_inspected_objects(context, [obj])
        
        if len(faces_distorted) > 0:
            # 添加到显示数据
            mesh_helpers.add_inspection_data(obj, faces_distorted, "DISTORTION")
            
            # 自动启用显示
            mesh_helpers.enable_display()
            
            result_msg = f"发现 {len(faces_distorted)} 个扭曲面"
            props.last_check_results = result_msg
        else:
            props.last_check_results = "未发现扭曲面"
        
        return {'FINISHED'}


class MESH_OT_ModelInspector_CheckAll(Operator):
    """全面检查"""
    bl_idname = "mesh.model_inspector_check_all"
    bl_label = "全面检查"
    bl_description = "根据设置执行所有检查（相交、扭曲等）"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.model_inspector
        selected_objects = get_objects_for_inspection(context)
        
        if not selected_objects:
            self.report({'ERROR'}, "请选择一个网格对象或确保之前检测过的对象仍存在于场景中")
            return {'CANCELLED'}
        
        # 检查是否有功能开启
        if not props.check_intersection and not props.check_distortion:
            self.report({'ERROR'}, "请至少开启一种检测功能")
            return {'CANCELLED'}
        
        # 清空之前的数据
        mesh_helpers.clear_inspection_data()
        
        total_intersect_faces = 0
        total_distorted_faces = 0
        
        # 执行检查
        for obj in selected_objects:
            # 1. 检查相交（如果启用）
            if props.check_intersection:
                if props.intersect_type == 'SELF':
                    faces_intersect = mesh_helpers.bmesh_check_self_intersect_object(
                        obj, threshold=props.intersect_threshold
                    )
                elif props.intersect_type == 'OBJECTS':
                    # 对象间相交检测
                    other_objects = [o for o in selected_objects if o != obj]
                    faces_intersect = mesh_helpers.bmesh_check_intersect_objects(
                        obj, other_objects, threshold=props.intersect_threshold
                    )
                else:  # BOTH
                    # 先检查自相交
                    faces_intersect = mesh_helpers.bmesh_check_self_intersect_object(
                        obj, threshold=props.intersect_threshold
                    )
                    # 再检查对象间相交
                    other_objects = [o for o in selected_objects if o != obj]
                    faces_intersect_between = mesh_helpers.bmesh_check_intersect_objects(
                        obj, other_objects, threshold=props.intersect_threshold
                    )
                    faces_intersect.extend(faces_intersect_between)
                
                if len(faces_intersect) > 0:
                    total_intersect_faces += len(faces_intersect)
                    mesh_helpers.add_inspection_data(obj, faces_intersect, "INTERSECT")
            
            # 2. 检查扭曲（如果启用）
            if props.check_distortion:
                faces_distorted = mesh_helpers.check_distorted_faces(
                    obj, angle_threshold=props.distortion_angle
                )
                if len(faces_distorted) > 0:
                    total_distorted_faces += len(faces_distorted)
                    mesh_helpers.add_inspection_data(obj, faces_distorted, "DISTORTION")
        
        # 更新检测对象记录
        update_last_inspected_objects(context, selected_objects)
        
        # 结果报告
        if total_intersect_faces > 0 or total_distorted_faces > 0:
            # 自动启用显示
            mesh_helpers.enable_display()
            
            result_parts = []
            if total_intersect_faces > 0:
                result_parts.append(f"{total_intersect_faces} 相交面")
            if total_distorted_faces > 0:
                result_parts.append(f"{total_distorted_faces} 扭曲面")
            
            result_msg = f"发现: {', '.join(result_parts)}"
            props.last_check_results = result_msg
        else:
            props.last_check_results = "未发现问题"
        
        return {'FINISHED'}


class MESH_OT_ModelInspector_ToggleDisplay(Operator):
    """切换颜色显示"""
    bl_idname = "mesh.model_inspector_toggle_display"
    bl_label = "切换颜色显示"
    bl_description = "开启或关闭问题区域的实时颜色显示"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        props = context.scene.model_inspector
        
        if mesh_helpers._is_display_enabled:
            mesh_helpers.disable_display()
        else:
            mesh_helpers.enable_display()
        
        return {'FINISHED'}


class MESH_OT_ModelInspector_SelectProblemFaces(Operator):
    """选择问题面片"""
    bl_idname = "mesh.model_inspector_select_faces"
    bl_label = "选择问题面片"
    bl_description = "在编辑模式下选择当前对象的问题面片"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "请选择一个网格对象")
            return {'CANCELLED'}
        
        if context.mode != 'EDIT_MESH':
            self.report({'ERROR'}, "请进入编辑模式")
            return {'CANCELLED'}
        
        # 查找当前对象的检测数据
        problem_faces = []
        for data in mesh_helpers._inspection_data:
            if data['object'] == obj:
                problem_faces.extend(data['faces'])
        
        if not problem_faces:
            self.report({'WARNING'}, "当前对象无检测数据")
            return {'CANCELLED'}
        
        # 进入面选择模式并选择问题面片
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.mesh.select_all(action='DESELECT')
        
        # 获取 bmesh 并选择问题面片
        bm = bmesh.from_edit_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        
        selected_count = 0
        for face_idx in problem_faces:
            if face_idx < len(bm.faces):
                bm.faces[face_idx].select = True
                selected_count += 1
        
        # 更新网格
        bmesh.update_edit_mesh(obj.data)
        
        return {'FINISHED'}


class MESH_OT_ModelInspector_CheckObjectIntersect(Operator):
    """检查对象间相交"""
    bl_idname = "mesh.model_inspector_check_objects"
    bl_label = "检查对象间相交"
    bl_description = "检测选中的多个对象之间的相交"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.model_inspector
        
        # 智能获取检测对象
        inspection_objects = get_objects_for_inspection(context)
        if not inspection_objects:
            self.report({'ERROR'}, "请选择网格对象或确保之前检测过的对象仍存在于场景中")
            return {'CANCELLED'}
        
        # 对象间相交检测需要至少2个对象，如果只恢复到1个对象，则提示用户选择更多对象
        if len(inspection_objects) < 2:
            if len(context.selected_objects) > 0:
                # 用户当前有选择但不是网格对象
                mesh_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
                if len(mesh_objects) < 2:
                    self.report({'ERROR'}, "请选择至少两个网格对象进行对象间相交检测")
                    return {'CANCELLED'}
                selected_objects = mesh_objects
            else:
                # 只能恢复到1个对象，提示用户选择更多
                self.report({'ERROR'}, "对象间相交检测需要至少两个对象，请选择更多网格对象")
                return {'CANCELLED'}
        else:
            selected_objects = inspection_objects
        
        # 清空之前的数据
        mesh_helpers.clear_inspection_data()
        
        total_faces = 0
        intersection_pairs = []
        
        # 检测每对对象之间的相交
        for i, obj1 in enumerate(selected_objects):
            other_objects = [obj for obj in selected_objects[i+1:]]
            faces_intersect = mesh_helpers.bmesh_check_intersect_objects(
                obj1, other_objects, threshold=props.intersect_threshold
            )
            
            if len(faces_intersect) > 0:
                total_faces += len(faces_intersect)
                mesh_helpers.add_inspection_data(obj1, faces_intersect, "INTERSECT")
                intersection_pairs.extend([(obj1.name, obj2.name) for obj2 in other_objects])
        
        # 更新检测对象记录
        update_last_inspected_objects(context, selected_objects)
        
        if total_faces > 0:
            # 自动启用显示
            mesh_helpers.enable_display()
            
            result_msg = f"发现 {total_faces} 个对象间相交面"
            props.last_check_results = result_msg
        else:
            props.last_check_results = "未发现对象间相交"
        
        return {'FINISHED'}


# 操作符类列表
classes = [
    MESH_OT_ModelInspector_CheckSelfIntersect,
    MESH_OT_ModelInspector_CheckObjectIntersect,
    MESH_OT_ModelInspector_CheckDistortion,
    MESH_OT_ModelInspector_CheckAll,
    MESH_OT_ModelInspector_ToggleDisplay,
    MESH_OT_ModelInspector_SelectProblemFaces,
]


def register():
    """注册操作符"""
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    """注销操作符"""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)