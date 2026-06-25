import bpy
import json

path = "./render_settings.json"

with open(path, "r") as f:
    settings = json.load(f)

scene = bpy.context.scene
render = scene.render

r = settings["render"]

render.engine = r["engine"]

render.resolution_x = r["resolution_x"]
render.resolution_y = r["resolution_y"]
render.resolution_percentage = r["resolution_percentage"]

render.fps = r["fps"]
render.fps_base = r["fps_base"]

scene.frame_start = r["frame_start"]
scene.frame_end = r["frame_end"]
scene.frame_step = r["frame_step"]

render.filepath = r["filepath"]

render.film_transparent = r["film_transparent"]
render.use_persistent_data = r["use_persistent_data"]

img = settings["image_settings"]

render.image_settings.file_format = img["file_format"]
render.image_settings.color_mode = img["color_mode"]
render.image_settings.color_depth = img["color_depth"]

try:
    render.image_settings.compression = img["compression"]
except:
    pass

try:
    render.image_settings.quality = img["quality"]
except:
    pass

if render.engine != "CYCLES":
    render.engine = "CYCLES"

bpy.context.view_layer.update()


c = scene.cycles
cyc = settings["cycles"]

c.samples = cyc["samples"]
c.preview_samples = cyc["preview_samples"]

c.use_adaptive_sampling = cyc["adaptive_sampling"]
c.adaptive_threshold = cyc["adaptive_threshold"]

try:
    c.preview_adaptive_threshold = cyc["preview_adaptive_threshold"]
except:
    pass

c.use_denoising = cyc["use_denoising"]

try:
    c.denoiser = cyc["denoiser"]
except:
    pass

try:
    c.use_preview_denoising = cyc["use_preview_denoising"]
except:
    pass

try:
    c.preview_denoiser = cyc["preview_denoiser"]
except:
    pass

c.max_bounces = cyc["max_bounces"]
c.diffuse_bounces = cyc["diffuse_bounces"]
c.glossy_bounces = cyc["glossy_bounces"]
c.transmission_bounces = cyc["transmission_bounces"]
c.volume_bounces = cyc["volume_bounces"]
c.transparent_max_bounces = cyc["transparent_max_bounces"]

c.device = cyc["device"]

try:
    c.seed = cyc["seed"]
except:
    pass

try:
    c.time_limit = cyc["time_limit"]
except:
    pass

try:
    c.pixel_filter_type = cyc["pixel_filter_type"]
except:
    pass

try:
    c.filter_width = cyc["filter_width"]
except:
    pass

try:
    c.use_auto_tile = cyc["use_auto_tile"]
except:
    pass

cm = settings["color_management"]

scene.view_settings.view_transform = cm["view_transform"]
scene.view_settings.look = cm["look"]
scene.view_settings.exposure = cm["exposure"]
scene.view_settings.gamma = cm["gamma"]

scene.display_settings.display_device = cm["display_device"]
