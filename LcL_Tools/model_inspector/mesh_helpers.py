"""
模型检测辅助功能模块
从 check_toolbox 的 mesh_helpers.py 移植并优化的模型检测功能
包含相交检测和扭曲检测功能
"""

import bmesh
import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils.geometry import tessellate_polygon as tessellate
import array
import mathutils

# GPU 着色器兼容性处理
if not bpy.app.background:
    if bpy.app.version >= (3, 4, 0):
        single_color_shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    else:
        single_color_shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
else:
    single_color_shader = None

# 全局变量
_inspection_data = []  # 重命名为更通用的检测数据
_draw_handler = None
_is_display_enabled = False
HAS_INSPECTION_DATA = False

# 默认颜色
COLOR_INTERSECT_FACE = (0.96, 0.25, 0.006, 0.6)  # 相交面：红色半透明
COLOR_INTERSECT_EDGE = (1.0, 0.5, 0.0, 0.8)      # 相交边：橙色
COLOR_DISTORTION_FACE = (0.97, 0.26, 0.28, 0.6)  # 扭曲面：粉红色半透明
COLOR_LINE_OUTLINE = (0.0, 0.0, 0.0, 0.3)        # 轮廓线：黑色


def draw_poly(points, rgba):
    """绘制多边形面"""
    if len(points) < 3:
        return
    batch = batch_for_shader(single_color_shader, "TRIS", {"pos": points})
    single_color_shader.bind()
    single_color_shader.uniform_float("color", rgba)
    batch.draw(single_color_shader)


def draw_points(points, rgba):
    """绘制点"""
    if len(points) == 0:
        return
    batch = batch_for_shader(single_color_shader, "POINTS", {"pos": points})
    single_color_shader.bind()
    single_color_shader.uniform_float("color", rgba)
    batch.draw(single_color_shader)


def draw_line(points, rgba):
    """绘制线条"""
    if len(points) < 2:
        return
    batch = batch_for_shader(single_color_shader, "LINES", {"pos": points})
    single_color_shader.bind()
    single_color_shader.uniform_float("color", rgba)
    batch.draw(single_color_shader)


def batch_from_points(points, draw_type):
    """从点创建批次"""
    return batch_for_shader(single_color_shader, draw_type, {"pos": points})


def draw_callback():
    """GPU 绘制回调函数 - 支持模型检测显示"""
    if not _is_display_enabled or not _inspection_data:
        return
    
    # Set GPU state
    gpu.state.blend_set('ALPHA')
    gpu.state.depth_test_set('LESS_EQUAL')
    
    props = bpy.context.scene.model_inspector
    
    # Draw all inspection object data
    for inspect_info in _inspection_data[:]:  # Use slice copy to avoid issues during iteration
        # Safe object access with ReferenceError handling
        obj = None
        try:
            obj = inspect_info.get('object')
            # Test if object reference is still valid
            if obj:
                _ = obj.name  # This will raise ReferenceError if object was deleted
        except ReferenceError:
            # Object was deleted, remove from list
            _inspection_data.remove(inspect_info)
            continue
        
        # Check if object still exists and is valid
        if not obj or not hasattr(obj, 'type') or obj.type != 'MESH':
            # Remove invalid object data from list
            _inspection_data.remove(inspect_info)
            continue
        
        # Additional safety check - ensure object is still in scene
        scene_objects = None
        try:
            scene_objects = bpy.context.scene.objects
            if obj.name not in scene_objects:
                _inspection_data.remove(inspect_info)
                continue
        except ReferenceError:
            # Object reference is invalid
            _inspection_data.remove(inspect_info)
            continue
            
        face_indices = inspect_info['faces']
        inspect_type = inspect_info.get('inspection_type', 'INTERSECT')
        
        # 根据检测功能开关状态过滤显示
        if inspect_type == 'INTERSECT' and not props.check_intersection:
            continue
        if inspect_type == 'DISTORTION' and not props.check_distortion:
            continue
        
        # 根据检测类型选择颜色
        if inspect_type == 'DISTORTION':
            face_color = tuple(props.distortion_face_color)
            edge_color = tuple(props.distortion_face_color)  # 扭曲检测使用同样的颜色
        else:  # INTERSECT
            face_color = tuple(props.intersect_face_color)
            edge_color = tuple(props.intersect_edge_color)
        
        # Get current frame mesh data (consistent with detection)
        if bpy.context.mode == 'EDIT_MESH' and obj == bpy.context.active_object:
            bm = bmesh.from_edit_mesh(obj.data)
            use_world_transform = True
            matrix_world = obj.matrix_world
        else:
            # Use evaluated mesh data for drawing
            bm = bmesh_copy_from_object(obj, transform=False, triangulate=False, apply_modifiers=True)
            use_world_transform = True
            matrix_world = obj.matrix_world
            
        bm.faces.ensure_lookup_table()
        
        # Collect face vertices and edge vertices
        face_vertices = []
        edge_vertices = []
        
        for face_idx in face_indices:
            if face_idx < len(bm.faces):
                face = bm.faces[face_idx]
                
                # Get face vertices (apply world transform)
                if use_world_transform:
                    verts = [matrix_world @ v.co for v in face.verts]
                else:
                    verts = [v.co for v in face.verts]
                
                # Handle face rendering
                if len(verts) == 3:
                    # Triangle direct draw
                    face_vertices.extend([v.to_3d() for v in verts])
                elif len(verts) >= 4:
                    # Polygon needs triangulation
                    # Use tessellate for triangulation
                    tessellated = tessellate([verts])
                    
                    for tri_indices in tessellated:
                        triangle = [verts[i] for i in tri_indices]
                        face_vertices.extend([v.to_3d() for v in triangle])
                
                # Collect edge vertices for outline
                for edge in face.edges:
                    if edge.is_valid:
                        if use_world_transform:
                            edge_verts = [matrix_world @ v.co for v in edge.verts]
                        else:
                            edge_verts = [v.co for v in edge.verts]
                        edge_vertices.extend([v.to_3d() for v in edge_verts])
        
        # Draw faces
        if face_vertices:
            draw_poly(face_vertices, face_color)
        
        # Draw edges
        if edge_vertices:
            draw_line(edge_vertices, edge_color)
        
        # Clean up resources
        if bpy.context.mode != 'EDIT_MESH' or obj != bpy.context.active_object:
            bm.free()
    
    # Restore GPU state
    gpu.state.blend_set('NONE')
    gpu.state.depth_test_set('LESS_EQUAL')


def enable_display():
    """启用相交颜色显示"""
    global _draw_handler, _is_display_enabled
    
    if _draw_handler is None and single_color_shader is not None:
        _draw_handler = bpy.types.SpaceView3D.draw_handler_add(
            draw_callback, (), 'WINDOW', 'POST_VIEW'
        )
        _is_display_enabled = True
        
        # 刷新视口
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()


def disable_display():
    """禁用相交颜色显示"""
    global _draw_handler, _is_display_enabled
    
    if _draw_handler is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_draw_handler, 'WINDOW')
        _draw_handler = None
        _is_display_enabled = False
        
        # 刷新视口
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()


def toggle_display():
    """切换相交颜色显示"""
    if _is_display_enabled:
        disable_display()
    else:
        enable_display()


def clear_inspection_data():
    """清空检测数据"""
    global _inspection_data
    _inspection_data.clear()
    
    # 刷新视口
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()


def add_inspection_data(obj, face_indices, inspection_type="INTERSECT"):
    """添加检测数据"""
    global _inspection_data
    _inspection_data.append({
        'object': obj,
        'faces': face_indices,
        'inspection_type': inspection_type
    })


# 兼容旧函数名
clear_intersection_data = clear_inspection_data
add_intersection_data = add_inspection_data


def bmesh_copy_from_object(obj, transform=True, triangulate=False, apply_modifiers=False):
    """
    从对象复制网格数据到 bmesh
    从 check_toolbox 移植的功能，支持骨骼动画和修改器
    """
    assert obj.type == 'MESH'
    
    if apply_modifiers:
        # 强制获取当前帧的评估网格（包括骨骼动画、修改器等）
        depsgraph = bpy.context.evaluated_depsgraph_get()
        obj_eval = obj.evaluated_get(depsgraph)
        me = obj_eval.to_mesh()
        bm = bmesh.new()
        bm.from_mesh(me)
        obj_eval.to_mesh_clear()
    else:
        me = obj.data
        if obj.mode == 'EDIT':
            bm_orig = bmesh.from_edit_mesh(me)
            bm = bm_orig.copy()
        else:
            bm = bmesh.new()
            bm.from_mesh(me)
    
    # 注意：当apply_modifiers=True时，评估网格已经包含了世界变换
    # 所以不需要再应用matrix_world
    if transform and not apply_modifiers:
        bm.transform(obj.matrix_world)
    if triangulate:
        bmesh.ops.triangulate(bm, faces=bm.faces)
    
    return bm


def bmesh_from_object(obj):
    """
    从对象获取 bmesh
    从 check_toolbox 移植的功能
    """
    me = obj.data
    is_editmode = (obj.mode == 'EDIT')
    
    if is_editmode:
        bm = bmesh.from_edit_mesh(me)
    else:
        bm = bmesh.new()
        bm.from_mesh(me)
    
    return bm


def bmesh_check_self_intersect_object(obj, threshold=0.00001):
    """
    检查对象的自相交
    从 check_toolbox 移植并优化的核心功能，支持动画模型
    
    Args:
        obj: Blender 对象
        threshold: BVH 树的精度阈值
    
    Returns:
        array.array: 相交面的索引数组
    """
    if not obj.data.polygons:
        return array.array('i', ())
    
    # 获取当前帧的评估后网格数据（支持动画和修改器）
    bm = bmesh_copy_from_object(obj, transform=False, triangulate=False, apply_modifiers=True)
    
    # 手动应用世界变换
    bm.transform(obj.matrix_world)
    
    # 创建 BVH 树进行相交检测
    tree = mathutils.bvhtree.BVHTree.FromBMesh(bm, epsilon=threshold)
    
    # 检测重叠的面
    overlap = tree.overlap(tree)
    
    # 提取相交的面索引
    faces_error = {i for i_pair in overlap for i in i_pair}
    
    bm.free()
    return array.array('i', faces_error)


def check_object_intersections(obj1, obj2, threshold=0.00001):
    """
    检查两个对象间的相交，支持动画模型
    
    Args:
        obj1, obj2: 要检查的两个对象
        threshold: BVH 树的精度阈值
    
    Returns:
        tuple: (obj1_faces, obj2_faces) 相交面的索引数组
    """
    if not (obj1.data.polygons and obj2.data.polygons):
        return array.array('i', ()), array.array('i', ())
    
    # 获取两个对象的 bmesh（支持动画和修改器）
    # 对于对象间检测，需要在各自的世界坐标系中处理
    bm1 = bmesh_copy_from_object(obj1, transform=False, triangulate=False, apply_modifiers=True)
    bm2 = bmesh_copy_from_object(obj2, transform=False, triangulate=False, apply_modifiers=True)
    
    # 手动应用世界变换（因为评估网格不包含世界变换）
    bm1.transform(obj1.matrix_world)
    bm2.transform(obj2.matrix_world)
    
    # 创建 BVH 树
    tree1 = mathutils.bvhtree.BVHTree.FromBMesh(bm1, epsilon=threshold)
    tree2 = mathutils.bvhtree.BVHTree.FromBMesh(bm2, epsilon=threshold)
    
    # 检测重叠
    overlap = tree1.overlap(tree2)
    
    # 分别提取两个对象的相交面
    obj1_faces = {pair[0] for pair in overlap}
    obj2_faces = {pair[1] for pair in overlap}
    
    bm1.free()
    bm2.free()
    
    return array.array('i', obj1_faces), array.array('i', obj2_faces)


def bmesh_check_intersect_objects(target_obj, other_objects, threshold=0.00001):
    """
    检查目标对象与其他对象的相交（兼容operators.py的调用方式）
    
    Args:
        target_obj: 目标对象
        other_objects: 其他对象列表
        threshold: BVH 树的精度阈值
    
    Returns:
        array.array: 目标对象中相交面的索引数组
    """
    if not other_objects:
        return array.array('i', ())
    
    all_intersect_faces = set()
    
    for other_obj in other_objects:
        if other_obj and other_obj.type == 'MESH' and other_obj != target_obj:
            target_faces, _ = check_object_intersections(target_obj, other_obj, threshold)
            all_intersect_faces.update(target_faces)
    
    return array.array('i', all_intersect_faces)


def face_is_distorted(face, angle_threshold):
    """
    检查面片是否扭曲（从 check_toolbox 移植）
    
    Args:
        face: bmesh face object
        angle_threshold: 角度阈值（弧度）
    
    Returns:
        bool: 如果面片扭曲则返回 True
    """
    face_normal = face.normal
    angle_fn = face_normal.angle
    
    for loop in face.loops:
        loop_normal = loop.calc_normal()
        if loop_normal.dot(face_normal) < 0.0:
            loop_normal.negate()
        
        # 计算角度差异
        angle_diff = angle_fn(loop_normal, 1000.0)  # 使用一个较大的fallback值
        if angle_diff > angle_threshold:
            return True
    
    return False


def check_distorted_faces(obj, angle_threshold):
    """
    检查对象的扭曲面片
    
    Args:
        obj: Blender 对象
        angle_threshold: 角度阈值（弧度）
    
    Returns:
        array.array: 扭曲面的索引数组
    """
    if not obj.data.polygons:
        return array.array('i', ())
    
    bm = bmesh_from_object(obj)
    bm.normal_update()
    
    distorted_faces = []
    for i, face in enumerate(bm.faces):
        if face_is_distorted(face, angle_threshold):
            distorted_faces.append(i)
    
    if obj.mode != 'EDIT':
        bm.free()
    
    return array.array('i', distorted_faces)


def cleanup_handlers():
    """清理所有 GPU 绘制句柄"""
    disable_display()
    clear_inspection_data()


def get_inspection_stats():
    """获取检测统计信息"""
    total_objects = len(set(data['object'] for data in _inspection_data))
    total_faces = sum(len(data['faces']) for data in _inspection_data)
    
    # 分类统计
    intersect_count = sum(len(data['faces']) for data in _inspection_data 
                         if data.get('inspection_type', 'INTERSECT') == 'INTERSECT')
    distortion_count = sum(len(data['faces']) for data in _inspection_data 
                          if data.get('inspection_type', 'DISTORTION') == 'DISTORTION')
    
    return {
        'objects_count': total_objects,
        'faces_count': total_faces,
        'intersect_faces': intersect_count,
        'distorted_faces': distortion_count,
        'is_display_enabled': _is_display_enabled
    }


def get_current_inspected_objects():
    """获取当前检测中的对象名称列表"""
    if not _inspection_data:
        return []
    
    # 获取当前有效的对象名称
    object_names = []
    for data in _inspection_data:
        obj = data.get('object')
        if obj:
            try:
                # 测试对象引用是否仍然有效
                name = obj.name
                if name not in object_names:
                    object_names.append(name)
            except ReferenceError:
                # 对象已被删除，跳过
                continue
    
    return object_names


def get_display_object_name(context):
    """获取用于显示的对象名称
    优先返回当前检测对象，如果没有则返回最后检测的对象"""
    
    # 优先获取当前检测的对象
    current_objects = get_current_inspected_objects()
    if current_objects:
        if len(current_objects) == 1:
            return current_objects[0]
        else:
            return f"{current_objects[0]} 等{len(current_objects)}个对象"
    
    # 如果没有当前检测数据，检查是否有选中的mesh对象
    selected_mesh_objects = [obj.name for obj in context.selected_objects if obj.type == 'MESH']
    if selected_mesh_objects:
        if len(selected_mesh_objects) == 1:
            return selected_mesh_objects[0]
        else:
            return f"{selected_mesh_objects[0]} 等{len(selected_mesh_objects)}个对象"
    
    # 最后尝试使用保存的最后检测对象
    if hasattr(context.scene, 'model_inspector'):
        last_objects = context.scene.model_inspector.last_inspected_objects
        if last_objects:
            return last_objects
    
    return "未选择对象"


# 兼容旧函数名
get_intersection_stats = get_inspection_stats
