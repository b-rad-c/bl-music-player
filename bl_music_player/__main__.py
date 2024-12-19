#!/usr/bin/env python3
import bpy
import sys
from pathlib import Path

file_dir = Path(__file__).parent
addon_dir = file_dir / 'addons'
blend_file = file_dir / 'startup.blend'

sys.path.append(addon_dir.as_posix())
from music_player.opsdata import cli_load_and_render


bpy.ops.wm.open_mainfile(filepath=str(blend_file))

#
# render test frame #
#

# bpy.context.scene.render.filepath = 'image.png' 
# bpy.context.scene.render.image_settings.file_format = 'PNG'
# bpy.ops.render.render(write_still=True)

music_file = addon_dir / 'music_player' / 'music' / 'Ketsa - You Best Boogie.mp3'

# load audio and render #
cli_load_and_render(str(music_file), bpy.context)


print('done.')