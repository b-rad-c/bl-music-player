# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****
#
# (c) 2021, Blender Foundation - Paul Golter

import subprocess
import sys
import os
import time
import math
from typing import Dict, Optional, Tuple
import bpy
import mido

#
# area functions
#

def find_area(context: bpy.types.Context, area_name: str) -> Optional[bpy.types.Area]:
    if isinstance(context, dict):
        # Handle override context.
        screen = context["screen"]
    else:
        screen = context.screen

    for area in screen.areas:
        # print(f'find_area: checking area {area.type} for {area_name}')
        if area.type == area_name:
            return area
    return None


def get_context_for_area(area: bpy.types.Area, region_type="WINDOW") -> Dict:
    for region in area.regions:
        if region.type == region_type:
            ctx = {}

            # In weird cases, e.G mouse over toolbar of filebrowser,
            # bpy.context.copy is None. Check for that.
            if bpy.context.copy:
                ctx = bpy.context.copy()

            ctx["area"] = area
            ctx["region"] = region
            ctx["screen"] = area.id_data
            return ctx
    return {}


def close_area(area: bpy.types.Area) -> None:
    bpy.ops.screen.area_close(get_context_for_area(area))

#
# sequencer functions
#

def del_all_sequences(context: bpy.types.Context) -> None:
    for seq_name in [s.name for s in context.scene.sequence_editor.sequences_all]:
        context.scene.sequence_editor.sequences.remove(
            context.scene.sequence_editor.sequences[seq_name]
        )

def fit_frame_range_to_strips(context: bpy.types.Context) -> Tuple[int, int]:
    """
    Fits frame range of active scene to exactly encapsulate all strips in the Sequence Editor.
    """

    def get_sort_tuple(strip) -> Tuple[int, int]:
        return (strip.frame_final_start, strip.frame_final_duration)
    
    scene = context.scene

    strips = scene.sequence_editor.sequences_all

    if not strips:
        scene.frame_start = 0
        scene.frame_end = 0
        return (0, 0)

    strips = list(strips)
    strips.sort(key=get_sort_tuple)

    scene.frame_start = strips[0].frame_final_start
    scene.frame_end = strips[-1].frame_final_end - 1

    return (scene.frame_start, scene.frame_end)

def load_and_bake_audio(context, sound_path:str, background:bool=False) -> None:

    print(f'music_player.play({sound_path})')

    # reset sequence
    bpy.ops.screen.animation_cancel()

    # if scene is not None:
    #     bpy.context.window.scene = bpy.data.scenes[scene]

    bpy.context.scene.frame_set(1)
    del_all_sequences(context)
    # add audio to sequence
    seq_area = find_area(bpy.context, 'SEQUENCE_EDITOR')
    seq_context = get_context_for_area(seq_area)
    with context.temp_override(**seq_context):
        bpy.ops.sequencer.sound_strip_add(
            filepath=sound_path,
            frame_start=1,
            channel=1
        )

    fit_frame_range_to_strips(context)  # seq_context does not have .scene as an attribute?

    if not background:
        with context.temp_override(**seq_context):
            bpy.ops.sequencer.view_all()
    
    graph_area = find_area(bpy.context, 'GRAPH_EDITOR')
    graph_context = get_context_for_area(graph_area)

    with context.temp_override(**graph_context):
        bpy.ops.object.select_all(action='DESELECT')

        bpy.data.screens["Default"].areas[3].spaces[0].dopesheet.show_only_selected = True

        print('\tbaking full...')
        bpy.data.objects['audio signal - full'].select_set(True)
        bpy.ops.graph.sound_to_samples(filepath=sound_path)
        bpy.data.objects['audio signal - full'].select_set(False)

        print('\tbaking low...')
        bpy.data.objects['audio signal - low'].select_set(True)
        bpy.ops.graph.sound_to_samples(filepath=sound_path, low=0, high=250)
        bpy.data.objects['audio signal - low'].select_set(False)

        print('\tbaking low mid...')
        bpy.data.objects['audio signal - low mid'].select_set(True)
        bpy.ops.graph.sound_to_samples(filepath=sound_path, low=250, high=400)
        bpy.data.objects['audio signal - low mid'].select_set(False)

        print('\tbaking high mid...')
        bpy.data.objects['audio signal - high mid'].select_set(True)
        bpy.ops.graph.sound_to_samples(filepath=sound_path, low=400, high=800)
        bpy.data.objects['audio signal - high mid'].select_set(False)

        print('\tbaking high...')
        bpy.data.objects['audio signal - high'].select_set(True)
        bpy.ops.graph.sound_to_samples(filepath=sound_path, low=800, high=100000)
        bpy.data.objects['audio signal - high'].select_set(False)

#
# audio functions
#

midi_device = 'bl-music-player-midi'

def samples_from_mic(gain_db=46.0, sample_rate=24, min_level=0.0001, quiet=True, window_size=None):
    """
    ffmpeg -f avfoundation -list_devices true -i ""
    ffmpeg -f avfoundation -i ":2" -ac 1 -ar 441000 -t 5 mic.wav

    NOTE: run this is a terminal outside of VSCode
    
    Args:
        gain_db: Gain in decibels (dB). 0 dB = no change, +6 dB = double, +20 dB = 10x
                 Typical range: 20-60 dB for microphone input
        sample_rate: Samples per second to read from microphone
        min_level: Minimum threshold below which level is set to 0
        quiet: Suppress ffmpeg output
        window_size: Number of samples to use for RMS calculation (defaults to sample_rate)
    """
    
    # Convert dB to linear gain (divide by 10 for power, 20 for amplitude)
    gain = 10 ** (gain_db / 10.0)
    
    # If no window_size specified, use sample_rate (1 second of samples)
    if window_size is None:
        window_size = sample_rate
    
    args = ['ffmpeg']
    if quiet:
        args += ['-loglevel', 'quiet']
    args += [
        '-f', 'avfoundation',
        '-i', ':2',
        '-f', 's16le',
        '-ac', '1',
        '-ar', f'{sample_rate}',
        '-'
    ]
    
    process = subprocess.Popen(args, stdout=subprocess.PIPE, shell=False)
    print(f'mic process started with PID: {process.pid}')

    max_value = (2 ** 16) / 2 - 1
    increment = 1 / max_value
    
    # Buffer to hold samples for RMS calculation
    sample_buffer = []

    try:
        while process.poll() is None:
            buffer = process.stdout.read(2)
            
            if buffer:
                # Get the raw sample value (keep signed for proper RMS)
                raw_value = int.from_bytes(buffer, 'little', signed=True) * increment
                sample_buffer.append(raw_value)
                
                # Once we have enough samples, calculate RMS
                if len(sample_buffer) >= window_size:
                    # Calculate RMS (Root Mean Square)
                    rms = (sum(s**2 for s in sample_buffer) / len(sample_buffer)) ** 0.5
                    
                    # Apply gain
                    level = rms * gain
                    
                    # Apply thresholding and clamping
                    if level < min_level:
                        level = 0.0
                    elif level > 1.0:
                        level = 1.0
                    
                    # print(f'level: {level:.5f}')
                    yield level
                    
                    # Clear buffer for next window
                    sample_buffer.clear()
            else:
                print('no more data from ffmpeg, exiting.')
                break

        process.wait()

    except KeyboardInterrupt:
        print('KeyboardInterrupt detected, terminating process...')
        yield 0.0
        process.kill()
        process.wait()

    except Exception as e:
        print(f'Error occurred: {e}')
        process.kill()
        process.wait()

    print('exiting samples_from_mic')

def midi_relay(gain_db=46.0, sample_rate=24, min_level=0.0001, window_size=None) -> None:
    port = mido.open_output(midi_device, virtual=True)
    try:
        for sample in samples_from_mic(gain_db=gain_db, sample_rate=sample_rate, min_level=min_level, window_size=window_size):
            port.send(mido.Message('control_change', channel=0, control=1, value=int(sample * 127)))
    finally:
        port.close()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='MIDI Relay - run this via cli and select sync from microphone in cli')
    parser.add_argument('--gain', '-g', type=float, default=25.0, help='Gain in decibels (dB). Typical range: 20-60 dB')
    parser.add_argument('--sample-rate', '-sr', type=int, default=60, help='Sample rate for microphone input')
    parser.add_argument('--min-level', '-ml', type=float, default=0.0001, help='Minimum level threshold')
    parser.add_argument('--window-size', '-ws', type=int, default=4, help='Window size for RMS calculation (defaults to sample_rate)')

    args = parser.parse_args()

    midi_relay(
        gain_db=args.gain,
        sample_rate=args.sample_rate,
        min_level=args.min_level,
        window_size=args.window_size
    )