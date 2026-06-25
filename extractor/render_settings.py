import bpy
import json
from pathlib import Path

scene = bpy.context.scene
render = scene.render
cycles = scene.cycles

data = {
    "scene_name": scene.name,

    "render": {
        "engine": render.engine,

        "resolution_x": render.resolution_x,
        "resolution_y": render.resolution_y,
        "resolution_percentage": render.resolution_percentage,

        "fps": render.fps,
        "fps_base": render.fps_base,

        "frame_start": scene.frame_start,
        "frame_end": scene.frame_end,
        "frame_step": scene.frame_step,

        "filepath": render.filepath,

        "film_transparent": render.film_transparent,
        "use_persistent_data": render.use_persistent_data,
    },

    "image_settings": {
        "file_format": render.image_settings.file_format,
        "color_mode": render.image_settings.color_mode,
        "color_depth": render.image_settings.color_depth,
        "compression": getattr(render.image_settings, "compression", None),
        "quality": getattr(render.image_settings, "quality", None),
    },

    "cycles": {
        "samples": cycles.samples,
        "adaptive_sampling": cycles.use_adaptive_sampling,
        "adaptive_threshold": cycles.adaptive_threshold,

        "use_denoising": cycles.use_denoising,
        "denoiser": cycles.denoiser,

        "preview_samples": cycles.preview_samples,
        "use_preview_denoising": getattr(cycles, "use_preview_denoising", None),
        "preview_denoiser": getattr(cycles, "preview_denoiser", None),
        "preview_adaptive_threshold": getattr(
            cycles,
            "preview_adaptive_threshold",
            None
        ),

        "max_bounces": cycles.max_bounces,
        "diffuse_bounces": cycles.diffuse_bounces,
        "glossy_bounces": cycles.glossy_bounces,
        "transmission_bounces": cycles.transmission_bounces,
        "volume_bounces": cycles.volume_bounces,
        "transparent_max_bounces": cycles.transparent_max_bounces,

        "use_auto_tile": getattr(cycles, "use_auto_tile", None),
        "device": cycles.device,

        "seed": cycles.seed,
        "time_limit": cycles.time_limit,
        "pixel_filter_type": cycles.pixel_filter_type,
        "filter_width": cycles.filter_width,
    },

    "color_management": {
        "view_transform": scene.view_settings.view_transform,
        "look": scene.view_settings.look,
        "exposure": scene.view_settings.exposure,
        "gamma": scene.view_settings.gamma,

        "display_device": scene.display_settings.display_device,
    },
}

outfile = Path(bpy.data.filepath).parent / "render_settings.json"

with open(outfile, "w") as f:
    json.dump(data, f, indent=4)