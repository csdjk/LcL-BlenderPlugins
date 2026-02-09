# BlenderToMax Sync Module
from . import properties
from . import operators
from . import ui


def register():
    """Register BlenderToMax"""
    properties.register()
    operators.register()
    ui.register()


def unregister():
    """Unregister BlenderToMax"""
    ui.unregister()
    operators.unregister()
    properties.unregister()
