#!/usr/bin/env python3
import bpy
import sys
import os
import time
import argparse
from contextlib import contextmanager
from pathlib import Path
from music_player.opsdata import load_and_bake_audio


# suprress stdout during render (ref: https://blender.stackexchange.com/a/270201/156811)
@contextmanager
def stdout_redirected(to=os.devnull):

    fd = sys.stdout.fileno()

    ##### assert that Python and C stdio write using the same file descriptor
    ####assert libc.fileno(ctypes.c_void_p.in_dll(libc, "stdout")) == fd == 1

    def _redirect_stdout(to):
        sys.stdout.close() # + implicit flush()
        os.dup2(to.fileno(), fd) # fd writes to 'to' file
        sys.stdout = os.fdopen(fd, 'w') # Python writes to fd

    with os.fdopen(os.dup(fd), 'w') as old_stdout:
        with open(to, 'w') as file:
            _redirect_stdout(to=file)
        try:
            yield # allow code to be run with the redirected stdout
        finally:
            _redirect_stdout(to=old_stdout) # restore stdout.
                                            # buffering and flags such as
                                            # CLOEXEC may be different


# contants #

src_dir = Path(__file__).parent
blend_file = src_dir / 'bl_music_player_app/startup.blend'
default_audio_file = src_dir / 'music_player' / 'music' / 'Ketsa - You Best Boogie.mp3'

# cli #

parser = argparse.ArgumentParser(description='Render a musical animation.')
parser.add_argument('--audio', '-a', type=str, help='Path to the audio file', default=str(default_audio_file))
parser.add_argument('--output', '-o', type=str, help='Path to the output file', default='output.mp4')

args = parser.parse_args()

if not os.path.exists(args.audio):
    raise FileNotFoundError(f'Audio file not found: {args.audio}')

if not args.output.endswith('.mp4'):
    raise ValueError('Output file must be an .mp4 file')

# load and bake audio #

bpy.ops.wm.open_mainfile(filepath=str(blend_file))
load_and_bake_audio(bpy.context, sound_path=os.path.abspath(args.audio), background=True)

# render #

bpy.context.scene.render.filepath = args.output

with stdout_redirected():
    start = time.time()
    bpy.ops.render.render(animation=True)
    end = time.time()

total_seconds = end - start
print('render time:', round(total_seconds / 60, 2), 'mins')
print('done.')
