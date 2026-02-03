"""
网格辅助功能模块
从 check_toolbox 的 mesh_helpers.py 移植并优化的相交检测功能
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
_intersection_data = []
_draw_handler = None
_is_display_enabled = False

# 默认颜色
COLOR_FACE_DEFAULT = (0.96, 0.25, 0.006, 0.6)  # 红色半透明面
COLOR_EDGE_DEFAULT = (1.0, 0.5, 0.0, 0.8)      # 橙色边框
COLOR_LINE_OUTLINE = (0.0, 0.0, 0.0, 0.3)      # 黑色轮廓线


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
    """GPU 绘制回调函数 - 支持动画模型显示"""
    if not _is_display_enabled or not _intersection_data:
        return
    
    # 设置 GPU 状态
    gpu.state.blend_set('ALPHA')
    gpu.state.depth_test_set('LESS_EQUAL')
    
    try:
        props = bpy.context.scene.intersection_detector
        
        # 绘制所有相交对象的数据
        for intersect_info in _intersection_data:
            obj = intersect_info['object']
            if not obj or obj.type != 'MESH':
                continue
                
            face_indices = intersect_info['faces']
            face_color = tuple(props.intersect_face_color)
            edge_color = tuple(props.intersect_edge_color)
            
            # 获取当前帧的评估网格数据（与检测时保持一致）
            if bpy.context.mode == 'EDIT_MESH' and obj == bpy.context.active_object:
                bm = bmesh.from_edit_mesh(obj.data)
                use_world_transform = True
                matrix_world = obj.matrix_world
            else:
                # 使用评估后的网格数据进行绘制
                bm = bmesh_copy_from_object(obj, transform=False, triangulate=False, apply_modifiers=True)
                use_world_transform = True
                matrix_world = obj.matrix_world
                
            bm.faces.ensure_lookup_table()
            
            # 收集面顶点和边顶点
            face_vertices = []
            edge_vertices = []
            
            for face_idx in face_indices:
                if face_idx < len(bm.faces):
                    face = bm.faces[face_idx]
                    
                    # 获取面的顶点（应用世界变换）
                    if use_world_transform:
                        verts = [matrix_world @ v.co for v in face.verts]
                    else:
                        verts = [v.co for v in face.verts]
                    
                    # 处理面的渲染
                    if len(verts) == 3:
                        # 三角形直接绘制
                        face_vertices.extend([v.to_3d() for v in verts])
                    elif len(verts) >= 4:
                        # 多边形需要三角化
                        try:
                            # 使用 tessellate 进行三角化
                            tessellated = tessellate([verts])
                            
                            for tri_indices in tessellated:
                                triangle = [verts[i] for i in tri_indices]
                                face_vertices.extend([v.to_3d() for v in triangle])
                                
                        except Exception as e:
                            print(f"三角化失败: {e}")
                            # 回退到扇形三角化
                            for i in range(1, len(verts) - 1):
                                triangle = [verts[0], verts[i], verts[i + 1]]
                                face_vertices.extend([v.to_3d() for v in triangle])
                    
                    # 收集边顶点用于轮廓
                    for edge in face.edges:
                        if edge.is_valid:
                            if use_world_transform:
                                edge_verts = [matrix_world @ v.co for v in edge.verts]
                            else:
                                edge_verts = [v.co for v in edge.verts]
                            edge_vertices.extend([v.to_3d() for v in edge_verts])
            
            # 绘制面
            if face_vertices:
                draw_poly(face_vertices, face_color)
            
            # 绘制边框
            if edge_vertices:
                draw_line(edge_vertices, edge_color)
            
            # 清理资源
            if bpy.context.mode != 'EDIT_MESH' or obj != bpy.context.active_object:
                bm.free()
                
    except Exception as e:
        print(f"绘制相交区域时发生错误: {e}")
    finally:
        # 恢复 GPU 状态
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
        try:
            bpy.types.SpaceView3D.draw_handler_remove(_draw_handler, 'WINDOW')
        except:
            pass
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


def clear_intersection_data():
    """清空相交数据"""
    global _intersection_data
    _intersection_data.clear()
    
    # 刷新视口
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()


def add_intersection_data(obj, face_indices, intersect_type="SELF"):
    """添加相交数据"""
    global _intersection_data
    _intersection_data.append({
        'object': obj,
        'faces': face_indices,
        'type': intersect_type
    })


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


def cleanup_handlers():
    """清理所有 GPU 绘制句柄"""
    disable_display()
    clear_intersection_data()


def get_intersection_stats():
    """获取相交统计信息"""
    total_objects = len(set(data['object'] for data in _intersection_data))
    total_faces = sum(len(data['faces']) for data in _intersection_data)
    
    return {
        'objects_count': total_objects,
        'faces_count': total_faces,
        'is_display_enabled': _is_display_enabled
    }