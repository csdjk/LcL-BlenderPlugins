# Model Inspector Module
from . import operators
from . import properties
from . import ui
from . import mesh_helpers


def register():
    """Register model inspector"""
    properties.register()
    operators.register()
    ui.register()


def unregister():
    """Unregister model inspector"""
    ui.unregister()
    operators.unregister()
    properties.unregister()
