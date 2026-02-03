# UI components for Intersection Detector
from .ui import *

def register():
    """Register UI components"""
    from . import ui
    ui.register()

def unregister():
    """Unregister UI components"""
    from . import ui
    ui.unregister()