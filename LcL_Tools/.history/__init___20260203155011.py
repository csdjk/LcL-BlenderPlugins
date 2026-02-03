# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import bpy
import bmesh
import random
from mathutils import Vector

bl_info = {
    "name": "ADDON_NAME",
    "author": "AUTHOR_NAME",
    "description": "",
    "blender": (2, 80, 0),
    "version": (0, 0, 1),
    "location": "",
    "warning": "",
    "category": "Generic",
}

class LCL_OT_RandomSpheres(bpy.types.Operator):
    """Generate 10 random spheres with random locations and sizes"""
    bl_idname = "mesh.lcl_random_spheres"
    bl_label = "Generate Random Spheres"
    bl_options = {'REGISTER', 'UNDO'}
    
    # Properties for customization
    sphere_count: bpy.props.IntProperty(# type: ignore
        name="Sphere Count",
        description="Number of spheres to generate",
        default=100,
        min=1,
        max=1000
    )
    
    min_radius: bpy.props.FloatProperty(# type: ignore
        name="Min Radius",
        description="Minimum sphere radius",
        default=0.5,
        min=0.01,
        max=50.0
    )
    
    max_radius: bpy.props.FloatProperty(# type: ignore
        name="Max Radius", 
        description="Maximum sphere radius",
        default=2.0,
        min=0.01,
        max=50.0
    )
    
    spread_range: bpy.props.FloatProperty(# type: ignore
        name="Spread Range",
        description="Range for random positioning",
        default=20.0,
        min=1.0,
        max=200.0
    )
    
    min_subdivisions: bpy.props.IntProperty(# type: ignore
        name="Min Subdivisions",
        description="Minimum subdivision level for sphere detail",
        default=2,
        min=1,
        max=6
    )
    
    max_subdivisions: bpy.props.IntProperty(# type: ignore
        name="Max Subdivisions", 
        description="Maximum subdivision level for sphere detail",
        default=4,
        min=1,
        max=6
    )
    
    deform_chance: bpy.props.FloatProperty(# type: ignore
        name="Deform Chance",
        description="Probability of applying random deformation (0-1)",
        default=0.3,
        min=0.0,
        max=1.0,
        subtype='FACTOR'
    )
    
    deform_strength: bpy.props.FloatProperty(# type: ignore
        name="Deform Strength",
        description="Strength of random deformation",
        default=0.1,
        min=0.0,
        max=1.0,
        subtype='FACTOR'
    )
    
    min_scale: bpy.props.FloatProperty(# type: ignore
        name="Min Scale",
        description="Minimum random scale factor",
        default=0.8,
        min=0.1,
        max=2.0
    )
    
    max_scale: bpy.props.FloatProperty(# type: ignore
        name="Max Scale",
        description="Maximum random scale factor", 
        default=1.2,
        min=0.1,
        max=2.0
    )
    
    keep_above_ground: bpy.props.BoolProperty(# type: ignore
        name="Keep Above Ground",
        description="Keep spheres above Z=0",
        default=True
    )

    def execute(self, context):
        # Clear existing selection
        bpy.ops.object.select_all(action='DESELECT')
        
        created_objects = []
        
        for i in range(self.sphere_count):
            # Create mesh and object
            mesh = bpy.data.meshes.new(f"RandomSphere_{i+1}")
            obj = bpy.data.objects.new(f"RandomSphere_{i+1}", mesh)
            
            # Link object to scene
            context.collection.objects.link(obj)
            
            # Create sphere geometry using bmesh
            bm = bmesh.new()
            
            # Random radius
            radius = random.uniform(self.min_radius, self.max_radius)
            
            # Create sphere with configurable subdivision levels
            subdivisions = random.randint(self.min_subdivisions, self.max_subdivisions)
            bmesh.ops.create_uvsphere(bm, u_segments=subdivisions*8, v_segments=subdivisions*4, radius=radius)
            
            # Optional: Add random deformation based on chance setting
            if random.random() < self.deform_chance:
                bmesh.ops.randomize(bm, geom=bm.verts, offset=radius * self.deform_strength)
            
            # Update mesh
            bm.to_mesh(mesh)
            bm.free()
            
            # Random position with configurable ground keeping
            z_min = 0 if self.keep_above_ground else -self.spread_range
            z_max = self.spread_range
            
            obj.location = Vector((
                random.uniform(-self.spread_range, self.spread_range),
                random.uniform(-self.spread_range, self.spread_range),
                random.uniform(z_min, z_max)
            ))
            
            # Random rotation
            import math
            obj.rotation_euler = (
                random.uniform(0, 2 * math.pi),
                random.uniform(0, 2 * math.pi),
                random.uniform(0, 2 * math.pi)
            )
            
            # Random scale variation using configurable range
            scale_factor = random.uniform(self.min_scale, self.max_scale)
            obj.scale = (scale_factor, scale_factor, scale_factor)
            
            created_objects.append(obj)
        
        # Select all created objects
        for obj in created_objects:
            obj.select_set(True)
        
        # Set the last object as active
        if created_objects:
            context.view_layer.objects.active = created_objects[-1]
        
        self.report({'INFO'}, f"Generated {self.sphere_count} random spheres")
        return {'FINISHED'}


class LCL_PT_Tools(bpy.types.Panel):
    """LcL Tools Panel"""
    bl_label = "LcL Tools"
    bl_idname = "VIEW3D_PT_lcl_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "LcL Tools"
    
    def draw(self, context):
        layout = self.layout
        
        # Random Spheres section
        box = layout.box()
        box.label(text="Random Generation", icon='MESH_UVSPHERE')
        
        # Operator button
        box.operator("mesh.lcl_random_spheres", text="Generate Random Spheres55555", icon='PLUS')
        
        # Quick settings
        col = box.column(align=True)
        col.label(text="Quick Settings:")
        
        row = col.row(align=True)
        op = row.operator("mesh.lcl_random_spheres", text="Small (5)")
        op.sphere_count = 5
        op.min_radius = 0.3
        op.max_radius = 0.8
        op.spread_range = 5.0
        
        op = row.operator("mesh.lcl_random_spheres", text="Medium (20)")
        op.sphere_count = 20
        op.min_radius = 1.0
        op.max_radius = 3.0
        op.spread_range = 15.0
        
        row = col.row(align=True)
        op = row.operator("mesh.lcl_random_spheres", text="Massive (100)", icon='FORCE_TURBULENCE')
        op.sphere_count = 100
        op.min_radius = 0.2
        op.max_radius = 1.5
        op.spread_range = 25.0
        op.deform_chance = 0.5


# Registration
classes = [
    LCL_OT_RandomSpheres,
    LCL_PT_Tools,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    print("LcL_BlenderTools registered")


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    print("LcL_BlenderTools unregistered")


if __name__ == "__main__":
    register()
