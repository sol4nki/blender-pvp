import bpy
import json
import random
import string
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone
# from dotenv import load_dotenv

# SUPABASE_URL = os.getenv("SUPABASE_URL")
# SUPABASE_ANON_KEY = os.getenv("SUPABASE_KEY")

PROMPTS = [
    "Render a neon cyberpunk street at night.",
    "Create a photorealistic studio portrait with softbox lighting.",
    "Design a futuristic spaceship interior.",
    "Make a stylized low-poly forest scene at sunset.",
    "Build a dramatic underwater cave with bioluminescent flora.",
    "Model a cozy Japanese tea room at golden hour.",
    "Recreate a brutalist concrete tower in a foggy morning.",
    "Design an alien marketplace with exotic lighting.",
]

_poll_handle = None


def sb_headers():
    return {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def sb_get(table, params=None):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=sb_headers(), method="GET")
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"[PvP] GET {table} error: {e}")
        return None


def sb_post(table, data):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, headers=sb_headers(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            result = json.loads(r.read().decode())
            return result[0] if isinstance(result, list) else result
    except Exception as e:
        print(f"[PvP] POST {table} error: {e}")
        return None


def sb_patch(table, params, data):
    url = f"{SUPABASE_URL}/rest/v1/{table}?" + urllib.parse.urlencode(params)
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, headers=sb_headers(), method="PATCH")
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            result = json.loads(r.read().decode())
            return result[0] if isinstance(result, list) else result
    except Exception as e:
        print(f"[PvP] PATCH {table} error: {e}")
        return None


def sb_delete(table, params):
    url = f"{SUPABASE_URL}/rest/v1/{table}?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=sb_headers(), method="DELETE")
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return True
    except Exception as e:
        print(f"[PvP] DELETE {table} error: {e}")
        return False


def parse_iso(ts):
    if not ts:
        return None
    ts = ts.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        return None


def now_utc():
    return datetime.now(timezone.utc)


def seconds_left_from(started_at_str, duration_min):
    started = parse_iso(started_at_str)
    if not started:
        return 0.0
    elapsed = (now_utc() - started).total_seconds()
    return max(0.0, duration_min * 60 - elapsed)


def format_time(seconds):
    s = int(seconds)
    return f"{s // 60}:{s % 60:02d}"


def wrap_text(text, max_chars=32):
    words = text.split()
    lines, current = [], ""
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


def gen_room_code():
    return "".join(random.choices(string.ascii_uppercase, k=4))


def get_or_create_player(name):
    result = sb_post("players", {"name": name})
    if result:
        return result.get("id")
    return None


def leave_current_room(context):
    scene = context.scene
    if scene.pvp_room_id and scene.pvp_player_id:
        sb_delete("room_players", {
            "room_id": f"eq.{scene.pvp_room_id}",
            "player_id": f"eq.{scene.pvp_player_id}",
        })
        room = sb_get("rooms", {"id": f"eq.{scene.pvp_room_id}", "select": "host_player_id,status,code"})
        if room:
            r = room[0]
            if r.get("host_player_id") == scene.pvp_player_id and r.get("status") == "waiting":
                remaining = sb_get("room_players", {"room_id": f"eq.{scene.pvp_room_id}", "select": "player_id"})
                if remaining:
                    new_host = remaining[0]["player_id"]
                    sb_patch("rooms", {"id": f"eq.{scene.pvp_room_id}"}, {"host_player_id": new_host})
                else:
                    if r.get("code") != "GLOBAL":
                        sb_delete("rooms", {"id": f"eq.{scene.pvp_room_id}"})
                    else:
                        sb_patch("rooms", {"id": f"eq.{scene.pvp_room_id}"}, {
                            "status": "waiting", "started_at": None,
                            "prompt": None, "host_player_id": None,
                        })
    reset_local_state(scene)


def reset_local_state(scene):
    scene.pvp_room_id = ""
    scene.pvp_room_code = ""
    scene.pvp_player_id = ""
    scene.pvp_status = "idle"
    scene.pvp_prompt = ""
    scene.pvp_seconds_left = 0.0
    scene.pvp_duration_min = 0
    scene.pvp_player_count = 0
    scene.pvp_is_host = False
    scene.pvp_exit_armed = False
    scene.pvp_prompt_visible = True
    scene.pvp_error = ""
    scene.pvp_submitted = False
    scene.pvp_vote_submission_id = ""
    scene.pvp_submissions_json = ""
    scene.pvp_votes_json = ""
    scene.pvp_winner_name = ""
    stop_poll()


def poll_room(context):
    scene = context.scene
    if not scene.pvp_room_id:
        return None

    rooms = sb_get("rooms", {
        "id": f"eq.{scene.pvp_room_id}",
        "select": "status,prompt,duration_min,started_at,host_player_id,voting_ends_at",
    })
    if not rooms:
        return 2.0
    room = rooms[0]
    status = room.get("status", "waiting")

    players = sb_get("room_players", {
        "room_id": f"eq.{scene.pvp_room_id}",
        "select": "player_id",
    })
    scene.pvp_player_count = len(players) if players else 0

    if status == "waiting":
        scene.pvp_status = "lobby"
        scene.pvp_is_host = room.get("host_player_id") == scene.pvp_player_id

    elif status == "active":
        scene.pvp_status = "ingame"
        scene.pvp_prompt = room.get("prompt", "")
        scene.pvp_duration_min = room.get("duration_min", 5)
        secs = seconds_left_from(room.get("started_at"), room.get("duration_min", 5))
        scene.pvp_seconds_left = secs
        scene.pvp_is_host = room.get("host_player_id") == scene.pvp_player_id
        if secs <= 0:
            scene.pvp_status = "submitting"

    elif status == "voting":
        scene.pvp_status = "voting"
        scene.pvp_is_host = room.get("host_player_id") == scene.pvp_player_id
        subs = sb_get("submissions", {
            "room_id": f"eq.{scene.pvp_room_id}",
            "select": "id,player_id,render_path",
        })
        scene.pvp_submissions_json = json.dumps(subs or [])
        existing_vote = sb_get("votes", {
            "room_id": f"eq.{scene.pvp_room_id}",
            "voter_id": f"eq.{scene.pvp_player_id}",
            "select": "submission_id",
        })
        if existing_vote:
            scene.pvp_vote_submission_id = existing_vote[0].get("submission_id", "")

    elif status == "finished":
        scene.pvp_status = "results"
        all_votes = sb_get("votes", {
            "room_id": f"eq.{scene.pvp_room_id}",
            "select": "submission_id",
        })
        all_subs = sb_get("submissions", {
            "room_id": f"eq.{scene.pvp_room_id}",
            "select": "id,player_id",
        })
        if all_votes and all_subs:
            tally = {}
            for v in all_votes:
                sid = v["submission_id"]
                tally[sid] = tally.get(sid, 0) + 1
            if tally:
                winning_sid = max(tally, key=lambda x: tally[x])
                for s in all_subs:
                    if s["id"] == winning_sid:
                        pdata = sb_get("players", {"id": f"eq.{s['player_id']}", "select": "name"})
                        if pdata:
                            scene.pvp_winner_name = pdata[0].get("name", "Unknown")

    for area in bpy.context.screen.areas:
        area.tag_redraw()
    return 2.0


_poll_handle = None


def start_poll():
    global _poll_handle
    stop_poll()
    def _tick():
        try:
            return poll_room(bpy.context)
        except Exception as e:
            print(f"[PvP] poll error: {e}")
            return 2.0
    _poll_handle = bpy.app.timers.register(_tick, first_interval=1.0)


def stop_poll():
    global _poll_handle
    if _poll_handle is not None:
        try:
            bpy.app.timers.unregister(_poll_handle)
        except Exception:
            pass
        _poll_handle = None


def init_props():
    S = bpy.types.Scene
    S.pvp_player_name = bpy.props.StringProperty(name="Name", default="Player")
    S.pvp_player_id = bpy.props.StringProperty(default="")
    S.pvp_room_id = bpy.props.StringProperty(default="")
    S.pvp_room_code = bpy.props.StringProperty(default="")
    S.pvp_room_code_input = bpy.props.StringProperty(name="Room Code", default="", maxlen=4)
    S.pvp_duration_input = bpy.props.EnumProperty(
        name="Duration",
        items=[("2", "2 min", ""), ("5", "5 min", ""), ("10", "10 min", "")],
        default="5",
    )
    S.pvp_status = bpy.props.StringProperty(default="idle")
    S.pvp_prompt = bpy.props.StringProperty(default="")
    S.pvp_seconds_left = bpy.props.FloatProperty(default=0.0)
    S.pvp_duration_min = bpy.props.IntProperty(default=0)
    S.pvp_player_count = bpy.props.IntProperty(default=0)
    S.pvp_is_host = bpy.props.BoolProperty(default=False)
    S.pvp_exit_armed = bpy.props.BoolProperty(default=False)
    S.pvp_prompt_visible = bpy.props.BoolProperty(default=True)
    S.pvp_error = bpy.props.StringProperty(default="")
    S.pvp_submitted = bpy.props.BoolProperty(default=False)
    S.pvp_render_path = bpy.props.StringProperty(
        name="Render Path", default="", subtype="FILE_PATH"
    )
    S.pvp_vote_submission_id = bpy.props.StringProperty(default="")
    S.pvp_submissions_json = bpy.props.StringProperty(default="")
    S.pvp_votes_json = bpy.props.StringProperty(default="")
    S.pvp_winner_name = bpy.props.StringProperty(default="")


def clear_props():
    props = [
        "pvp_player_name", "pvp_player_id", "pvp_room_id", "pvp_room_code",
        "pvp_room_code_input", "pvp_duration_input", "pvp_status", "pvp_prompt",
        "pvp_seconds_left", "pvp_duration_min", "pvp_player_count", "pvp_is_host",
        "pvp_exit_armed", "pvp_prompt_visible", "pvp_error", "pvp_submitted",
        "pvp_render_path", "pvp_vote_submission_id", "pvp_submissions_json",
        "pvp_votes_json", "pvp_winner_name",
    ]
    for p in props:
        if hasattr(bpy.types.Scene, p):
            try:
                delattr(bpy.types.Scene, p)
            except Exception:
                pass


class PVP_OT_join_global(bpy.types.Operator):
    bl_idname = "pvp.join_global"
    bl_label = "Quick Join"

    @classmethod
    def poll(cls, context):
        return context.scene.pvp_status == "idle"

    def execute(self, context):
        scene = context.scene
        scene.pvp_error = ""
        player_id = get_or_create_player(scene.pvp_player_name)
        if not player_id:
            scene.pvp_error = "Could not register player."
            return {'CANCELLED'}
        scene.pvp_player_id = player_id

        rooms = sb_get("rooms", {"code": "eq.GLOBAL", "select": "id,status,host_player_id"})
        if not rooms:
            scene.pvp_error = "Could not reach server."
            return {'CANCELLED'}
        room = rooms[0]
        room_id = room["id"]

        sb_post("room_players", {"room_id": room_id, "player_id": player_id})

        if not room.get("host_player_id"):
            sb_patch("rooms", {"id": f"eq.{room_id}"}, {"host_player_id": player_id})

        scene.pvp_room_id = room_id
        scene.pvp_room_code = "GLOBAL"
        scene.pvp_status = "lobby"
        start_poll()
        return {'FINISHED'}


class PVP_OT_create_room(bpy.types.Operator):
    bl_idname = "pvp.create_room"
    bl_label = "Create Room"

    @classmethod
    def poll(cls, context):
        return context.scene.pvp_status == "idle"

    def execute(self, context):
        scene = context.scene
        scene.pvp_error = ""
        player_id = get_or_create_player(scene.pvp_player_name)
        if not player_id:
            scene.pvp_error = "Could not register player."
            return {'CANCELLED'}
        scene.pvp_player_id = player_id

        code = gen_room_code()
        duration = int(scene.pvp_duration_input)
        room = sb_post("rooms", {
            "code": code,
            "status": "waiting",
            "duration_min": duration,
            "host_player_id": player_id,
        })
        if not room:
            scene.pvp_error = "Could not create room."
            return {'CANCELLED'}

        room_id = room["id"]
        sb_post("room_players", {"room_id": room_id, "player_id": player_id})
        scene.pvp_room_id = room_id
        scene.pvp_room_code = code
        scene.pvp_status = "lobby"
        start_poll()
        return {'FINISHED'}


class PVP_OT_join_room(bpy.types.Operator):
    bl_idname = "pvp.join_room"
    bl_label = "Join Room"

    @classmethod
    def poll(cls, context):
        return context.scene.pvp_status == "idle" and len(context.scene.pvp_room_code_input) == 4

    def execute(self, context):
        scene = context.scene
        scene.pvp_error = ""
        code = scene.pvp_room_code_input.upper()

        rooms = sb_get("rooms", {"code": f"eq.{code}", "select": "id,status"})
        if not rooms:
            scene.pvp_error = f"Room '{code}' not found."
            return {'CANCELLED'}
        room = rooms[0]
        if room["status"] not in ("waiting",):
            scene.pvp_error = "That room is already in progress."
            return {'CANCELLED'}

        player_id = get_or_create_player(scene.pvp_player_name)
        if not player_id:
            scene.pvp_error = "Could not register player."
            return {'CANCELLED'}
        scene.pvp_player_id = player_id

        sb_post("room_players", {"room_id": room["id"], "player_id": player_id})
        scene.pvp_room_id = room["id"]
        scene.pvp_room_code = code
        scene.pvp_status = "lobby"
        start_poll()
        return {'FINISHED'}


class PVP_OT_start_game(bpy.types.Operator):
    bl_idname = "pvp.start_game"
    bl_label = "Start Game"

    @classmethod
    def poll(cls, context):
        s = context.scene
        return s.pvp_status == "lobby" and s.pvp_is_host and s.pvp_player_count >= 2

    def execute(self, context):
        scene = context.scene
        prompt = random.choice(PROMPTS)
        sb_patch("rooms", {"id": f"eq.{scene.pvp_room_id}"}, {
            "status": "active",
            "prompt": prompt,
            "started_at": now_utc().isoformat(),
        })
        return {'FINISHED'}


class PVP_OT_exit_game(bpy.types.Operator):
    bl_idname = "pvp.exit_game"
    bl_label = "Exit"

    @classmethod
    def poll(cls, context):
        return context.scene.pvp_status not in ("idle",)

    def execute(self, context):
        scene = context.scene
        if not scene.pvp_exit_armed:
            scene.pvp_exit_armed = True
            return {'FINISHED'}
        leave_current_room(context)
        return {'FINISHED'}


class PVP_OT_submit_render(bpy.types.Operator):
    bl_idname = "pvp.submit_render"
    bl_label = "Submit Render"

    @classmethod
    def poll(cls, context):
        s = context.scene
        return s.pvp_status == "submitting" and not s.pvp_submitted and bool(s.pvp_render_path)

    def execute(self, context):
        scene = context.scene
        result = sb_post("submissions", {
            "room_id": scene.pvp_room_id,
            "player_id": scene.pvp_player_id,
            "render_path": scene.pvp_render_path,
        })
        if result:
            scene.pvp_submitted = True
            self.report({'INFO'}, "Render submitted!")
        else:
            self.report({'ERROR'}, "Submission failed.")
        return {'FINISHED'}


class PVP_OT_end_voting(bpy.types.Operator):
    bl_idname = "pvp.end_voting"
    bl_label = "End Voting"

    @classmethod
    def poll(cls, context):
        s = context.scene
        return s.pvp_status == "voting" and s.pvp_is_host

    def execute(self, context):
        scene = context.scene
        sb_patch("rooms", {"id": f"eq.{scene.pvp_room_id}"}, {"status": "finished"})
        return {'FINISHED'}


class PVP_OT_open_voting(bpy.types.Operator):
    bl_idname = "pvp.open_voting"
    bl_label = "Open Voting"

    @classmethod
    def poll(cls, context):
        s = context.scene
        return s.pvp_status == "submitting" and s.pvp_is_host

    def execute(self, context):
        scene = context.scene
        sb_patch("rooms", {"id": f"eq.{scene.pvp_room_id}"}, {"status": "voting"})
        scene.pvp_status = "voting"
        return {'FINISHED'}


class PVP_OT_cast_vote(bpy.types.Operator):
    bl_idname = "pvp.cast_vote"
    bl_label = "Vote"
    submission_id: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        s = context.scene
        return s.pvp_status == "voting" and not s.pvp_vote_submission_id

    def execute(self, context):
        scene = context.scene
        if scene.pvp_vote_submission_id:
            self.report({'WARNING'}, "Already voted.")
            return {'CANCELLED'}
        result = sb_post("votes", {
            "room_id": scene.pvp_room_id,
            "voter_id": scene.pvp_player_id,
            "submission_id": self.submission_id,
        })
        if result:
            scene.pvp_vote_submission_id = self.submission_id
            self.report({'INFO'}, "Vote cast!")
        else:
            self.report({'ERROR'}, "Vote failed.")
        return {'FINISHED'}


class PVP_OT_play_again(bpy.types.Operator):
    bl_idname = "pvp.play_again"
    bl_label = "Play Again"

    def execute(self, context):
        leave_current_room(context)
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
        status = scene.pvp_status

        row = layout.row(align=True)
        row.label(text="Player", icon="USER")
        row.prop(scene, "pvp_player_name", text="")

        layout.separator(factor=0.4)

        if scene.pvp_error:
            box = layout.box()
            box.alert = True
            box.label(text=scene.pvp_error, icon="ERROR")
            layout.separator(factor=0.3)

        if status == "idle":
            self._draw_idle(layout, scene)
        elif status == "lobby":
            self._draw_lobby(layout, scene)
        elif status == "ingame":
            self._draw_ingame(layout, scene)
        elif status == "submitting":
            self._draw_submitting(layout, scene)
        elif status == "voting":
            self._draw_voting(layout, scene)
        elif status == "results":
            self._draw_results(layout, scene)

    def _draw_idle(self, layout, scene):
        layout.label(text="Quick Join", icon="WORLD")
        layout.operator("pvp.join_global", icon="FILE_REFRESH")

        layout.separator()
        layout.label(text="Private Room", icon="LOCKED")

        col = layout.column(align=True)
        col.prop(scene, "pvp_duration_input", text="Duration")
        col.operator("pvp.create_room", icon="ADD")

        layout.separator(factor=0.4)

        row = layout.row(align=True)
        row.prop(scene, "pvp_room_code_input", text="Code")
        row.operator("pvp.join_room", text="Join", icon="IMPORT")

    def _draw_lobby(self, layout, scene):
        box = layout.box()
        col = box.column(align=True)
        col.label(text=f"Room: {scene.pvp_room_code}", icon="LINKED")
        col.label(text=f"Players: {scene.pvp_player_count}", icon="COMMUNITY")
        if scene.pvp_is_host:
            col.label(text="You are the host", icon="CROWN")

        layout.separator(factor=0.4)

        if scene.pvp_is_host:
            col2 = layout.column()
            if scene.pvp_player_count < 2:
                col2.label(text="Waiting for players...", icon="TIME")
            col2.operator("pvp.start_game", icon="PLAY")
        else:
            layout.label(text="Waiting for host to start...", icon="TIME")

        layout.separator(factor=0.4)
        self._draw_exit(layout, scene)

    def _draw_ingame(self, layout, scene):
        seconds = scene.pvp_seconds_left
        is_red = seconds <= 30
        is_warn = 30 < seconds <= 60

        box = layout.box()
        col = box.column(align=True)
        col.label(text=f"Room {scene.pvp_room_code}  ·  {scene.pvp_player_count} players", icon="PLAY")

        timer_row = col.row()
        timer_row.scale_y = 2.0
        timer_row.alert = is_red
        timer_row.label(text=f"  {'🔴' if is_red else '⏱'}  {format_time(seconds)}")

        if is_warn:
            col.label(text="  ⚠  Under 1 minute left!")

        layout.separator(factor=0.4)

        prompt_row = layout.row(align=True)
        prompt_row.label(text="Prompt", icon="TEXT")
        prompt_row.operator(
            "pvp.toggle_prompt" if False else "pvp.exit_game",
            text="",
            icon="HIDE_OFF" if scene.pvp_prompt_visible else "HIDE_ON",
            emboss=False,
        )

        pbox = layout.box()
        pcol = pbox.column(align=True)
        pcol.scale_y = 0.85
        for line in wrap_text(scene.pvp_prompt):
            pcol.label(text=line)

        layout.separator(factor=0.4)
        self._draw_exit(layout, scene)

    def _draw_submitting(self, layout, scene):
        layout.label(text="Time's up! Submit your render.", icon="RENDER_STILL")
        layout.separator(factor=0.3)

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Prompt:", icon="TEXT")
        col.scale_y = 0.85
        for line in wrap_text(scene.pvp_prompt):
            col.label(text=line)

        layout.separator(factor=0.3)

        if not scene.pvp_submitted:
            layout.prop(scene, "pvp_render_path")
            layout.operator("pvp.submit_render", icon="EXPORT")
        else:
            layout.label(text="Render submitted!", icon="CHECKMARK")
            layout.label(text="Waiting for others...", icon="TIME")

        if scene.pvp_is_host:
            layout.separator(factor=0.3)
            layout.operator("pvp.open_voting", icon="HAND")

        layout.separator(factor=0.4)
        self._draw_exit(layout, scene)

    def _draw_voting(self, layout, scene):
        layout.label(text="Vote for the best render!", icon="HAND")
        layout.separator(factor=0.3)

        try:
            subs = json.loads(scene.pvp_submissions_json) if scene.pvp_submissions_json else []
        except Exception:
            subs = []

        already_voted = bool(scene.pvp_vote_submission_id)

        for sub in subs:
            box = layout.box()
            col = box.column(align=True)
            col.label(text=sub.get("render_path", "No path"), icon="IMAGE_DATA")

            is_mine = sub.get("player_id") == scene.pvp_player_id
            is_voted = sub.get("id") == scene.pvp_vote_submission_id

            row = col.row()
            if is_voted:
                row.label(text="Your vote", icon="CHECKMARK")
            elif is_mine:
                row.label(text="Your submission", icon="USER")
            elif not already_voted:
                op = row.operator("pvp.cast_vote", text="Vote for this", icon="HAND")
                op.submission_id = sub.get("id", "")
            else:
                row.label(text="", icon="BLANK1")

        if scene.pvp_is_host:
            layout.separator(factor=0.3)
            layout.operator("pvp.end_voting", icon="CHECKMARK")

        layout.separator(factor=0.4)
        self._draw_exit(layout, scene)

    def _draw_results(self, layout, scene):
        box = layout.box()
        col = box.column(align=True)
        col.scale_y = 1.3
        col.label(text="Round Over!", icon="TROPHY")
        if scene.pvp_winner_name:
            col.label(text=f"Winner: {scene.pvp_winner_name}", icon="FUND")
        else:
            col.label(text="No votes cast.", icon="INFO")

        layout.separator(factor=0.4)
        layout.operator("pvp.play_again", icon="FILE_REFRESH")

    def _draw_exit(self, layout, scene):
        col = layout.column()
        if scene.pvp_exit_armed:
            col.alert = True
            col.label(text="Press again to confirm exit", icon="ERROR")
        col.operator(
            "pvp.exit_game",
            text="Confirm Exit" if scene.pvp_exit_armed else "Exit Game",
            icon="CANCEL",
        )


class PVP_OT_toggle_prompt(bpy.types.Operator):
    bl_idname = "pvp.toggle_prompt"
    bl_label = "Toggle Prompt"

    def execute(self, context):
        context.scene.pvp_prompt_visible = not context.scene.pvp_prompt_visible
        return {'FINISHED'}


classes = (
    PVP_OT_join_global,
    PVP_OT_create_room,
    PVP_OT_join_room,
    PVP_OT_start_game,
    PVP_OT_exit_game,
    PVP_OT_submit_render,
    PVP_OT_open_voting,
    PVP_OT_end_voting,
    PVP_OT_cast_vote,
    PVP_OT_play_again,
    PVP_OT_toggle_prompt,
    PVP_PT_main_panel,
)


def register():
    init_props()
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    stop_poll()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    clear_props()