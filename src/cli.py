#!/usr/bin/env python3
import bpy
import time
from pathlib import Path
from music_player.opsdata import load_and_bake_audio

src_dir = Path(__file__).parent
blend_file = src_dir / 'bl_music_player_app/startup.blend'
music_file = src_dir / 'music_player' / 'music' / 'Ketsa - You Best Boogie.mp3'

# init #

bpy.ops.wm.open_mainfile(filepath=str(blend_file))
load_and_bake_audio(bpy.context, sound_path=music_file.as_posix(), background=True)

# render #

start = time.time()
bpy.ops.render.render(animation=True)
end = time.time()
print('render time:', round(end - start, 2), 'seconds')
print('done.')
