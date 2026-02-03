"""
相交检测器操作符
从 check_toolbox 移植并优化的相交检测操作
"""

import bpy
from bpy.types import Operator
from bpy.props import EnumProperty, StringProperty
import bmesh
from . import mesh_helpers


class MESH_OT_IntersectionDetector_ShowMessage(Operator):
    """显示消息弹窗"""
    bl_idname = "mesh.intersection_detector_show_message"
    bl_label = "提示"
    bl_description = "显示提示信息"
    
    message: StringProperty( #type: ignore
        name="消息",
        description="要显示的消息内容",
        default=""
    )
    
    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)
    
    def draw(self, context):
        layout = self.layout
        layout.label(text="", icon='INFO')
        
        # 将消息按行分割显示
        for line in self.message.split('\\n'):
            layout.label(text=line)


class MESH_OT_IntersectionDetector_CheckSelfIntersect(Operator):
    """检查自相交"""
    bl_idname = "mesh.intersection_detector_check_self"
    bl_label = "检查自相交"
    bl_description = "检测当前对象的自相交面"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.intersection_detector
        obj = context.active_object
        
        if not obj:
            self.report({'WARNING'}, "❌ 没有选中任何对象！请先选择一个网格对象进行检测")
            # 弹窗提示
            bpy.ops.mesh.intersection_detector_show_message('INVOKE_DEFAULT', 
                                         message="没有选中任何对象！\\n\\n请先选择一个网格对象进行自相交检测。")
            return {'CANCELLED'}
        
        if obj.type != 'MESH':
            self.report({'WARNING'}, f"❌ 选中的对象 '{obj.name}' 不是网格对象！请选择网格对象进行检测")
            # 弹窗提示  
            bpy.ops.mesh.intersection_detector_show_message('INVOKE_DEFAULT',
                                         message=f"选中的对象 '{obj.name}' 不是网格对象！\\n\\n请选择网格(Mesh)对象进行自相交检测。")
            return {'CANCELLED'}
        
        
        # 清空之前的数据
        mesh_helpers.clear_intersection_data()
        
        # 执行自相交检测
        faces_intersect = mesh_helpers.bmesh_check_self_intersect_object(
            obj, threshold=props.intersect_threshold
        )
        
        if len(faces_intersect) > 0:
            # 添加到显示数据
            mesh_helpers.add_intersection_data(obj, faces_intersect, "SELF")
            
            # 如果启用了颜色显示，自动开启
            if props.show_color_display:
                mesh_helpers.enable_display()
            
            result_msg = f"发现 {len(faces_intersect)} 个自相交面"
            props.last_check_results = result_msg
            self.report({'INFO'}, result_msg)
        else:
            props.last_check_results = "未发现自相交"
            self.report({'INFO'}, "未发现自相交")
        
        return {'FINISHED'}


class MESH_OT_IntersectionDetector_CheckObjectIntersect(Operator):
    """检查对象间相交"""
    bl_idname = "mesh.intersection_detector_check_objects"
    bl_label = "检查对象间相交"
    bl_description = "检测选中的多个对象之间的相交"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.intersection_detector
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        if len(selected_objects) == 0:
            self.report({'WARNING'}, "❌ 没有选中任何对象！请选择至少两个网格对象进行检测")
            # 弹窗提示
            bpy.ops.mesh.intersection_detector_show_message('INVOKE_DEFAULT', 
                                         message="没有选中任何对象！\\n\\n请选择至少两个网格对象进行对象间相交检测。")
            return {'CANCELLED'}
        elif len(selected_objects) < 2:
            self.report({'WARNING'}, f"❌ 只选中了 {len(selected_objects)} 个对象！需要至少两个网格对象")
            # 弹窗提示
            bpy.ops.mesh.intersection_detector_show_message('INVOKE_DEFAULT',
                                         message=f"只选中了 {len(selected_objects)} 个对象！\\n\\n对象间相交检测需要选择至少两个网格对象。")
            return {'CANCELLED'}
        
        
        # 清空之前的数据
        mesh_helpers.clear_intersection_data()
        
        intersection_count = 0
        intersection_pairs = []
        
        # 检测每对对象之间的相交
        for i, obj1 in enumerate(selected_objects):
            for obj2 in selected_objects[i+1:]:
                obj1_faces, obj2_faces = mesh_helpers.check_object_intersections(
                    obj1, obj2, threshold=props.intersect_threshold
                )
                
                if len(obj1_faces) > 0 or len(obj2_faces) > 0:
                    intersection_count += 1
                    intersection_pairs.append((obj1.name, obj2.name))
                    
                    # 添加到显示数据
                    if len(obj1_faces) > 0:
                        mesh_helpers.add_intersection_data(obj1, obj1_faces, "BETWEEN")
                    if len(obj2_faces) > 0:
                        mesh_helpers.add_intersection_data(obj2, obj2_faces, "BETWEEN")
        
        if intersection_count > 0:
            # 如果启用了颜色显示，自动开启
            if props.show_color_display:
                mesh_helpers.enable_display()
            
            result_msg = f"发现 {intersection_count} 对相交对象"
            props.last_check_results = result_msg
            self.report({'INFO'}, result_msg)
            
            # 打印详细信息
            for pair in intersection_pairs:
                print(f"相交对象: {pair[0]} ↔ {pair[1]}")
        else:
            props.last_check_results = "未发现对象间相交"
            self.report({'INFO'}, "未发现对象间相交")
        
        return {'FINISHED'}


class MESH_OT_IntersectionDetector_CheckAll(Operator):
    """全面检查相交"""
    bl_idname = "mesh.intersection_detector_check_all"
    bl_label = "全面检查"
    bl_description = "同时检查自相交和对象间相交"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.intersection_detector
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        if not selected_objects:
            self.report({'WARNING'}, "❌ 没有选中任何对象！请选择至少一个网格对象进行检测")
            # 弹窗提示
            bpy.ops.mesh.intersection_detector_show_message('INVOKE_DEFAULT', 
                                         message="没有选中任何对象！\\n\\n请选择至少一个网格对象进行全面相交检测。")
            return {'CANCELLED'}
        
        # 清空之前的数据
        mesh_helpers.clear_intersection_data()
        
        total_self_intersect = 0
        total_object_intersect = 0
        
        # 1. 检查自相交
        for obj in selected_objects:
            faces_intersect = mesh_helpers.bmesh_check_self_intersect_object(
                obj, threshold=props.intersect_threshold
            )
            if len(faces_intersect) > 0:
                total_self_intersect += len(faces_intersect)
                mesh_helpers.add_intersection_data(obj, faces_intersect, "SELF")
        
        # 2. 检查对象间相交
        if len(selected_objects) >= 2:
            for i, obj1 in enumerate(selected_objects):
                for obj2 in selected_objects[i+1:]:
                    obj1_faces, obj2_faces = mesh_helpers.check_object_intersections(
                        obj1, obj2, threshold=props.intersect_threshold
                    )
                    
                    if len(obj1_faces) > 0:
                        total_object_intersect += len(obj1_faces)
                        mesh_helpers.add_intersection_data(obj1, obj1_faces, "BETWEEN")
                    if len(obj2_faces) > 0:
                        total_object_intersect += len(obj2_faces)
                        mesh_helpers.add_intersection_data(obj2, obj2_faces, "BETWEEN")
        
        # 结果报告
        if total_self_intersect > 0 or total_object_intersect > 0:
            if props.show_color_display:
                mesh_helpers.enable_display()
            
            result_parts = []
            if total_self_intersect > 0:
                result_parts.append(f"{total_self_intersect} 个自相交面")
            if total_object_intersect > 0:
                result_parts.append(f"{total_object_intersect} 个对象间相交面")
            
            result_msg = f"发现: {', '.join(result_parts)}"
            props.last_check_results = result_msg
            self.report({'INFO'}, result_msg)
        else:
            props.last_check_results = "未发现任何相交"
            self.report({'INFO'}, "未发现任何相交")
        
        return {'FINISHED'}


class MESH_OT_IntersectionDetector_ToggleDisplay(Operator):
    """切换颜色显示"""
    bl_idname = "mesh.intersection_detector_toggle_display"
    bl_label = "切换颜色显示"
    bl_description = "开启或关闭相交区域的实时颜色显示"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        props = context.scene.intersection_detector
        
        if mesh_helpers._is_display_enabled:
            mesh_helpers.disable_display()
            props.show_color_display = False
            self.report({'INFO'}, "相交颜色显示已关闭")
        else:
            mesh_helpers.enable_display()
            props.show_color_display = True
            self.report({'INFO'}, "相交颜色显示已开启")
        
        return {'FINISHED'}


class MESH_OT_IntersectionDetector_ClearData(Operator):
    """清空相交数据"""
    bl_idname = "mesh.intersection_detector_clear_data"
    bl_label = "清空数据"
    bl_description = "清空所有相交检测数据"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        props = context.scene.intersection_detector
        mesh_helpers.clear_intersection_data()
        props.last_check_results = "数据已清空"
        self.report({'INFO'}, "相交数据已清空")
        return {'FINISHED'}


class MESH_OT_IntersectionDetector_SelectIntersected(Operator):
    """选择相交面"""
    bl_idname = "mesh.intersection_detector_select_intersected"
    bl_label = "选择相交面"
    bl_description = "在编辑模式下选择当前对象的相交面"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "请选择一个网格对象")
            return {'CANCELLED'}
        
        if context.mode != 'EDIT_MESH':
            self.report({'ERROR'}, "请进入编辑模式")
            return {'CANCELLED'}
        
        # 查找当前对象的相交数据
        intersected_faces = []
        for data in mesh_helpers._intersection_data:
            if data['object'] == obj:
                intersected_faces.extend(data['faces'])
        
        if not intersected_faces:
            self.report({'WARNING'}, "当前对象没有相交数据")
            return {'CANCELLED'}
        
        # 进入面选择模式并选择相交面
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.mesh.select_all(action='DESELECT')
        
        # 获取 bmesh 并选择相交面
        bm = bmesh.from_edit_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        
        selected_count = 0
        for face_idx in intersected_faces:
            if face_idx < len(bm.faces):
                bm.faces[face_idx].select = True
                selected_count += 1
        
        # 更新网格
        bmesh.update_edit_mesh(obj.data)
        
        self.report({'INFO'}, f"已选择 {selected_count} 个相交面")
        return {'FINISHED'}


# 自动更新相关的操作符和模态处理器
class MESH_OT_IntersectionDetector_AutoUpdate(Operator):
    """自动更新模态处理器"""
    bl_idname = "mesh.intersection_detector_auto_update"
    bl_label = "自动更新相交检测"
    bl_description = "启用编辑模式下的自动相交检测"
    
    _timer = None
    
    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'
    
    def modal(self, context, event):
        props = context.scene.intersection_detector
        
        if not props.auto_update or context.mode != 'EDIT_MESH':
            self.cancel(context)
            return {'FINISHED'}
        
        if event.type == 'TIMER':
            obj = context.active_object
            if obj and obj.type == 'MESH':
                # 执行快速的自相交检测
                try:
                    faces_intersect = mesh_helpers.bmesh_check_self_intersect_object(
                        obj, threshold=props.intersect_threshold
                    )
                    
                    # 更新显示数据
                    mesh_helpers.clear_intersection_data()
                    if len(faces_intersect) > 0:
                        mesh_helpers.add_intersection_data(obj, faces_intersect, "SELF")
                        
                        if props.show_color_display:
                            mesh_helpers.enable_display()
                except:
                    pass  # 忽略错误，避免影响编辑流程
        
        return {'PASS_THROUGH'}
    
    def execute(self, context):
        wm = context.window_manager
        self._timer = wm.event_timer_add(time_step=2.0, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
    def cancel(self, context):
        wm = context.window_manager
        if self._timer:
            wm.event_timer_remove(self._timer)
        return {'CANCELLED'}


# 算子类列表
classes = [
    MESH_OT_IntersectionDetector_ShowMessage,
    MESH_OT_IntersectionDetector_CheckSelfIntersect,
    MESH_OT_IntersectionDetector_CheckObjectIntersect,
    MESH_OT_IntersectionDetector_CheckAll,
    MESH_OT_IntersectionDetector_ToggleDisplay,
    MESH_OT_IntersectionDetector_ClearData,
    MESH_OT_IntersectionDetector_SelectIntersected,
    MESH_OT_IntersectionDetector_AutoUpdate,
]


def register():
    """注册操作符"""
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    """注销操作符"""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)