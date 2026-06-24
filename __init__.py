bl_info = {
    "name": "Blender PvP",
    "blender": (4, 0, 0),
    "category": "3D View",
}

from . import ui

def register():
    ui.register()

def unregister():
    ui.unregister()

