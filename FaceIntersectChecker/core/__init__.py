# Core functionality for Intersection Detector
from .mesh_helpers import *
from .operators import *
from .properties import *

def register():
    """Register core components"""
    from . import operators
    from . import properties
    
    properties.register()
    operators.register()

def unregister():
    """Unregister core components"""
    from . import operators
    from . import properties
    
    operators.unregister()
    properties.unregister()