"""
LcL Tools - Blender Plugin Main Entry
"""

import bpy

from . import model_inspector
from . import blender_to_max


bl_info = {
    "name": "LcL Tools",
    "blender": (4, 0, 0),
    "category": "Mesh",
    "version": (1, 0, 0),
    "author": "LcL Team",
    "description": "LcL Tools - Model Inspector and Blender-to-Max Sync Tool",
    "location": "View3D > Sidebar > LcL",
    "doc_url": "",
    "tracker_url": "",
    "support": "COMMUNITY"
}


def register():
    """Register plugin"""
    # Register modules (order determines UI display order)
    blender_to_max.register()      # BlenderToMax at top
    model_inspector.register()     # Model inspector below


def unregister():
    """Unregister plugin"""
    # Unregister modules (reverse order)
    model_inspector.unregister()
    blender_to_max.unregister()


if __name__ == "__main__":
    register()