import bpy

class PVP_OT_login(bpy.types.Operator):
    bl_idname = "pvp.login"
    bl_label = "Login"

    def execute(self, context):
        self.report({'INFO'}, "Login clicked")
        return {'FINISHED'}


class PVP_OT_find_match(bpy.types.Operator):
    bl_idname = "pvp.find_match"
    bl_label = "Find Match"

    def execute(self, context):
        self.report({'INFO'}, "Finding match...")
        return {'FINISHED'}


class PVP_OT_start_game(bpy.types.Operator):
    bl_idname = "pvp.start_game"
    bl_label = "Start Game"

    def execute(self, context):
        self.report({'INFO'}, "Game started")
        return {'FINISHED'}


class PVP_OT_render(bpy.types.Operator):
    bl_idname = "pvp.render"
    bl_label = "Render"

    def execute(self, context):
        self.report({'INFO'}, "Rendering...")
        return {'FINISHED'}


class PVP_OT_submit(bpy.types.Operator):
    bl_idname = "pvp.submit"
    bl_label = "Submit"

    def execute(self, context):
        self.report({'INFO'}, "Submitted render")
        return {'FINISHED'}

class PVP_PT_main_panel(bpy.types.Panel):
    bl_label = "PvP Blender"
    bl_idname = "PVP_PT_main_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "PvP"

    def draw(self, context):
        layout = self.layout

        layout.label(text="Blender PvP Prototype")

        layout.separator()

        layout.operator("pvp.login", icon="USER")
        layout.operator("pvp.find_match", icon="VIEWZOOM")
        layout.operator("pvp.start_game", icon="PLAY")

        layout.separator()

        layout.operator("pvp.render", icon="RENDER_STILL")
        layout.operator("pvp.submit", icon="EXPORT")

        layout.separator()

        layout.label(text="Debug Mode Active")

classes = (
    PVP_OT_login,
    PVP_OT_find_match,
    PVP_OT_start_game,
    PVP_OT_render,
    PVP_OT_submit,
    PVP_PT_main_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)