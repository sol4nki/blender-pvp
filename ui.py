import bpy
import random
import runpy
import os


PROMPTS = [
    "Render a neon cyberpunk street at night.",
    "Create a photorealistic studio portrait with softbox lighting.",
    "Design a futuristic spaceship interior.",
    "Make a stylized low-poly forest scene at sunset.",
    "Build a dramatic underwater cave with bioluminescent flora.",
    "Model a cozy Japanese tea room at golden hour.",
    # just add random stuff or idk
]

_timer_handle = None


def init_props():
    scene = bpy.types.Scene

    scene.pvp_player_name = bpy.props.StringProperty(
        name="Player Name",
        default = f"User{random.randint(0, 999):03d}"
    )
    scene.pvp_active_prompt = bpy.props.StringProperty(
        name="Prompt",
        default=""
    )
    scene.pvp_in_game = bpy.props.BoolProperty(
        name="In Game",
        default=False
    )
    scene.pvp_game_duration = bpy.props.IntProperty(
        name="Game Duration (min)",
        default=0
    )
    scene.pvp_seconds_left = bpy.props.FloatProperty(
        name="Seconds Left",
        default=0.0
    )
    scene.pvp_exit_armed = bpy.props.BoolProperty(
        name="Exit Armed",
        default=False
    )
    scene.pvp_prompt_visible = bpy.props.BoolProperty(
        name="Prompt Visible",
        default=True
    )


def clear_props():
    props = [
        "pvp_player_name", "pvp_active_prompt", "pvp_in_game",
        "pvp_game_duration", "pvp_seconds_left", "pvp_exit_armed",
        "pvp_prompt_visible",
    ]
    for p in props:
        if hasattr(bpy.types.Scene, p):
            try:
                delattr(bpy.types.Scene, p)
            except Exception:
                pass


def start_timer():
    global _timer_handle
    stop_timer()
    _timer_handle = bpy.app.timers.register(tick, first_interval=1.0)


def stop_timer():
    global _timer_handle
    if _timer_handle is not None:
        try:
            bpy.app.timers.unregister(_timer_handle)
        except Exception:
            pass
        _timer_handle = None


def tick():
    scene = bpy.context.scene
    if not scene.pvp_in_game:
        return None
    scene.pvp_seconds_left = max(0.0, scene.pvp_seconds_left - 1.0)
    for area in bpy.context.screen.areas:
        area.tag_redraw()
    if scene.pvp_seconds_left <= 0:
        scene.pvp_in_game = False
        scene.pvp_exit_armed = False
        stop_timer()
        return None
    return 1.0


def start_game(context, duration_min):
    scene = context.scene
    scene.pvp_in_game = True
    scene.pvp_exit_armed = False
    scene.pvp_game_duration = duration_min
    scene.pvp_seconds_left = float(duration_min * 60)
    scene.pvp_active_prompt = random.choice(PROMPTS)
    scene.pvp_prompt_visible = True
    start_timer()


def format_time(seconds):
    s = int(seconds)
    m = s // 60
    s = s % 60
    return f"{m}:{s:02d}"


def wrap_text(text, max_chars=34):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        if len(current) + len(word) + (1 if current else 0) <= max_chars:
            current = current + (" " if current else "") + word
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


class PVP_OT_join_random(bpy.types.Operator):
    bl_idname = "pvp.join_random"
    bl_label = "Random"

    @classmethod
    def poll(cls, context):
        return not context.scene.pvp_in_game

    def execute(self, context):
        start_game(context, random.choice([2, 5, 10]))
        self.report({'INFO'}, "Joined random game")
        return {'FINISHED'}


class PVP_OT_join_2min(bpy.types.Operator):
    bl_idname = "pvp.join_2min"
    bl_label = "2 min"

    @classmethod
    def poll(cls, context):
        return not context.scene.pvp_in_game

    def execute(self, context):
        start_game(context, 2)
        return {'FINISHED'}


class PVP_OT_join_5min(bpy.types.Operator):
    bl_idname = "pvp.join_5min"
    bl_label = "5 min"

    @classmethod
    def poll(cls, context):
        return not context.scene.pvp_in_game

    def execute(self, context):
        start_game(context, 5)
        return {'FINISHED'}


class PVP_OT_join_10min(bpy.types.Operator):
    bl_idname = "pvp.join_10min"
    bl_label = "10 min"

    @classmethod
    def poll(cls, context):
        return not context.scene.pvp_in_game

    def execute(self, context):
        start_game(context, 10)
        return {'FINISHED'}


class PVP_OT_exit_game(bpy.types.Operator):
    bl_idname = "pvp.exit_game"
    bl_label = "Exit Game"

    @classmethod
    def poll(cls, context):
        return context.scene.pvp_in_game

    def execute(self, context):
        scene = context.scene
        if not scene.pvp_exit_armed:
            scene.pvp_exit_armed = True
            self.report({'WARNING'}, "Press Exit again to confirm")
            return {'FINISHED'}
        scene.pvp_in_game = False
        scene.pvp_exit_armed = False
        scene.pvp_active_prompt = ""
        scene.pvp_seconds_left = 0.0
        scene.pvp_game_duration = 0
        stop_timer()
        self.report({'INFO'}, "Exited game")
        return {'FINISHED'}


class PVP_OT_toggle_prompt(bpy.types.Operator):
    bl_idname = "pvp.toggle_prompt"
    bl_label = "Toggle Prompt"

    def execute(self, context):
        context.scene.pvp_prompt_visible = not context.scene.pvp_prompt_visible
        return {'FINISHED'}


class PVP_OT_apply_render_settings(bpy.types.Operator):
    bl_idname = "pvp.apply_render_settings"
    bl_label = "Apply Render Preset"

    def execute(self, context):
        path = os.path.join(
            os.path.dirname(__file__),
            "extractor",
            "apply_render_settings.py"
        )
        runpy.run_path(path)
        self.report({'INFO'}, "Render settings applied")
        return {'FINISHED'}


class PVP_PT_main_panel(bpy.types.Panel):
    bl_label = "Blender PvP"
    bl_idname = "PVP_PT_main_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "PvP"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        header_row = layout.row(align=True)
        header_row.label(text="Name")
        header_row.prop(scene, "pvp_player_name", text="")

        layout.separator(factor=0.5)

        if not scene.pvp_in_game:
            self._draw_lobby(layout, scene)
        else:
            self._draw_ingame(layout, scene)

        layout.separator()
        col = layout.column()
        col.label(text="Tools", icon="TOOL_SETTINGS")
        col.operator("pvp.apply_render_settings", icon="RENDER_STILL")

    def _draw_lobby(self, layout, scene):
        col = layout.column(align=False)
        col.label(text="Matchmaking", icon="WORLD")

        col.separator(factor=0.3)
        col.operator("pvp.join_random", icon="FILE_REFRESH")

        row = col.row(align=True)
        row.scale_y = 1.2

        op2 = row.operator("pvp.join_2min", text="2 min")
        op5 = row.operator("pvp.join_5min", text="5 min")
        op10 = row.operator("pvp.join_10min", text="10 min")

    def _draw_ingame(self, layout, scene):
        seconds = scene.pvp_seconds_left
        time_str = format_time(seconds)
        is_red = seconds <= 30
        is_yellow = 30 < seconds <= 60

        layout.separator(factor=0.3)

        timer_box = layout.box()
        timer_col = timer_box.column(align=True)

        dur_label = f"{scene.pvp_game_duration} min game  ·  {scene.pvp_player_name}"
        timer_col.label(text=dur_label, icon="PLAY")

        timer_row = timer_col.row()
        timer_row.scale_y = 2.2
        timer_row.alert = is_red
        timer_row.label(
            text=f"  ⏱  {time_str}" if not is_red else f"  🔴  {time_str}",
            icon="NONE"
        )

        if is_yellow and not is_red:
            timer_col.label(text="  ⚠  Under 1 minute left!", icon="NONE")

        layout.separator(factor=0.5)

        prompt_header = layout.row(align=True)
        prompt_header.label(text="Prompt", icon="TEXT")
        toggle_icon = "HIDE_OFF" if scene.pvp_prompt_visible else "HIDE_ON"
        prompt_header.operator("pvp.toggle_prompt", text="", icon=toggle_icon, emboss=False)

        if scene.pvp_prompt_visible:
            prompt_box = layout.box()
            prompt_col = prompt_box.column(align=True)
            prompt_col.scale_y = 0.85
            for line in wrap_text(scene.pvp_active_prompt, max_chars=32):
                prompt_col.label(text=line)

        layout.separator(factor=0.5)

        exit_col = layout.column()
        if scene.pvp_exit_armed:
            exit_col.alert = True
            exit_col.label(text="Press again to confirm exit", icon="ERROR")
        exit_col.operator(
            "pvp.exit_game",
            text="Confirm Exit" if scene.pvp_exit_armed else "Exit Game",
            icon="CANCEL"
        )


classes = (
    PVP_OT_join_random,
    PVP_OT_join_2min,
    PVP_OT_join_5min,
    PVP_OT_join_10min,
    PVP_OT_exit_game,
    PVP_OT_toggle_prompt,
    PVP_OT_apply_render_settings,
    PVP_PT_main_panel,
)


def register():
    init_props()
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    stop_timer()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    clear_props()