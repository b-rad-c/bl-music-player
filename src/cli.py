#!/usr/bin/env python3
# import bpy
import sys
import os
import time
import argparse
import multiprocessing
import subprocess

from tempfile import TemporaryDirectory
from contextlib import contextmanager
from pathlib import Path


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


def render_thread(threads:int, thread_num:int, audio:Path, tmp_frame_dir:Path):
    with stdout_redirected():
        import bpy
        from music_player.opsdata import load_and_bake_audio

        bpy.ops.wm.open_mainfile(filepath=str(blend_file))
        load_and_bake_audio(bpy.context, sound_path=str(audio.absolute()), background=True)

        bpy.context.scene.render.filepath = str(tmp_frame_dir / 'frame-')

        print('rendering: ', bpy.context.scene.render.filepath)

        if threads > 1:
            bpy.context.scene.frame_start = thread_num
            bpy.context.scene.frame_step = threads
    
        bpy.ops.render.render(animation=True)


def main(threads:int, audio:Path, output:Path):

    with TemporaryDirectory() as tmp_frame_dir:
        tmp_frame_dir_path = Path(tmp_frame_dir)

        frame_start = time.time()

        if threads == 1:
            render_thread(1, 1, audio, tmp_frame_dir_path)
        else:
            process_args = [(threads, i, audio, tmp_frame_dir_path) for i in range(1, threads + 1)]
            with multiprocessing.Pool(processes=threads) as pool:
                pool_result = pool.starmap_async(render_thread, process_args)
                pool.close()
                pool.join()

                if not pool_result.successful():
                    raise RuntimeError('Render failed')

        frame_end = time.time()

        frame_total = frame_end - frame_start
        print('frame render time:', round(frame_total / 60, 2), 'mins')

        ff_start = time.time()
        ff_args = ['ffmpeg', '-i', tmp_frame_dir_path / 'frame-%04d.png', '-i', audio, '-map', '0:v', '-map', '1:a', output.absolute()]
        subprocess.run(ff_args, check=True)
        ff_end = time.time()
        ff_total = ff_end - ff_start
        
        total_seconds = frame_total + ff_total
        print('ffmpeg time:', round(ff_total / 60, 2), 'mins')
        print('total time:', round(total_seconds / 60, 2), 'mins')
        print('done.')

if __name__ == '__main__':
    multiprocessing.freeze_support()

    # cli #

    parser = argparse.ArgumentParser(description='Render a musical animation.')
    parser.add_argument('--audio', '-a', type=Path, help='Path to the audio file', default=str(default_audio_file))
    parser.add_argument('--output', '-o', type=Path, help='Path to the output file', default='output.mp4')
    parser.add_argument('--threads', '-t', type=int, help='Number of threads to use (default=8)', default=8)

    args = parser.parse_args()

    if not os.path.exists(args.audio):
        raise FileNotFoundError(f'Audio file not found: {args.audio}')

    if args.output.suffix != '.mp4':
        raise ValueError('Output file must be an .mp4 file')
    
    main(args.threads, args.audio, args.output)
