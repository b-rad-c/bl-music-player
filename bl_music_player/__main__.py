#!/usr/bin/env python3
import bpy
import sys
import time
from pathlib import Path

file_dir = Path(__file__).parent
addon_dir = file_dir / 'addons'
blend_file = file_dir / 'startup.blend'

sys.path.append(addon_dir.as_posix())
from music_player.opsdata import load_and_bake_audio


bpy.ops.wm.open_mainfile(filepath=str(blend_file))

#
# render test frame #
#

# bpy.context.scene.render.filepath = 'image.png' 
# bpy.context.scene.render.image_settings.file_format = 'PNG'
# bpy.ops.render.render(write_still=True)

music_file = addon_dir / 'music_player' / 'music' / 'Ketsa - You Best Boogie.mp3'

# load audio and render #
load_and_bake_audio(bpy.context, sound_path=music_file.as_posix(), background=True)

start = time.time()
bpy.ops.render.render(animation=True)
end = time.time()
print('render time:', round(end - start, 2), 'seconds')

print('done.')
