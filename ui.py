import bpy
import runpy
import os


class PVP_OT_apply_render_settings(bpy.types.Operator):
    bl_idname = "pvp.apply_render_settings"
    bl_label = "Apply Render Settings"

    def execute(self, context):
        try:
            path = os.path.join(
                os.path.dirname(__file__),
                "extractor",
                "apply_render_settings.py"
            )

            runpy.run_path(path)

            self.report({'INFO'}, "Render settings applied")
        except Exception as e:
            self.report({'ERROR'}, str(e))

        return {'FINISHED'}


class PVP_OT_reset_render(bpy.types.Operator):
    bl_idname = "pvp.reset_render"
    bl_label = "Reset Render Settings"

    def execute(self, context):
        scene = bpy.context.scene
        render = scene.render

        # Reset to Eevee defaults
        render.engine = 'BLENDER_EEVEE_NEXT' if hasattr(bpy.types, "BLENDER_EEVEE_NEXT") else 'BLENDER_EEVEE'

        render.resolution_x = 1920
        render.resolution_y = 1080
        render.resolution_percentage = 100

        render.fps = 24
        render.fps_base = 1.0

        scene.frame_start = 1
        scene.frame_end = 250
        scene.frame_step = 1

        if hasattr(scene, "cycles"):
            c = scene.cycles
            c.samples = 128
            c.use_adaptive_sampling = False
            c.use_denoising = False

        self.report({'INFO'}, "Reset to default Eevee settings")
        return {'FINISHED'}


class PVP_PT_main_panel(bpy.types.Panel):
    bl_label = "Blender PvP"
    bl_idname = "PVP_PT_main_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "PvP"

    def draw(self, context):
        layout = self.layout

        layout.label(text="Render Controls")

        layout.operator("pvp.apply_render_settings", icon="RENDER_STILL")
        layout.operator("pvp.reset_render", icon="LOOP_BACK")

        layout.separator()
        layout.label(text="PvP Prototype")


classes = (
    PVP_OT_apply_render_settings,
    PVP_OT_reset_render,
    PVP_PT_main_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)