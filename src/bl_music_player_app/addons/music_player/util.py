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
from typing import Dict, Optional, Tuple, NamedTuple
from dataclasses import dataclass
import bpy
import mido
import numpy as np

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

MIDI_DEVICE_NAME = 'bl-music-player-midi'

class FrequencyBands(NamedTuple):
    """Audio levels for 4-band EQ."""
    low: float       # Bass: 20-250 Hz
    low_mid: float   # Low-mid: 250-2000 Hz
    high_mid: float  # High-mid: 2000-6000 Hz
    high: float      # Treble: 6000-20000 Hz

@dataclass
class MicSampleConfig:
    """Configuration for microphone sampling and processing."""
    gain_db: float = 46.0
    sample_rate: int = 44100  # Higher sample rate needed for FFT
    fft_size: int = 2048  # Window size for FFT (power of 2)
    min_level: float = 0.0001
    quiet: bool = True
    smoothing: float = 0.0
    compression_threshold: float = 0.7
    compression_ratio: float = 4.0
    use_fft: bool = True  # If False, use simple RMS

def samples_from_mic(config: MicSampleConfig):
    """
    ffmpeg -f avfoundation -list_devices true -i ""
    ffmpeg -f avfoundation -i ":2" -ac 1 -ar 441000 -t 5 mic.wav

    NOTE: run this is a terminal outside of VSCode
    
    Args:
        config: MicSampleConfig containing:
            gain_db: Gain in decibels (dB). 0 dB = no change, +6 dB = double, +20 dB = 10x
                     Typical range: 20-60 dB for microphone input
            sample_rate: Samples per second to read from microphone
            fft_size: Window size for FFT analysis (power of 2, e.g., 2048)
            min_level: Minimum threshold below which level is set to 0
            quiet: Suppress ffmpeg output
            smoothing: Exponential smoothing factor (0.0-1.0). 0=no smoothing, 0.5=moderate, 0.9=heavy
            compression_threshold: Level above which compression is applied (0.0-1.0)
            compression_ratio: Ratio of compression above threshold (1.0=none, 4.0=4:1, inf=limiting)
            use_fft: If True, yield FrequencyBands; if False, yield single RMS value
    
    Yields:
        FrequencyBands if use_fft=True, otherwise float
    """
    
    # Convert dB to linear gain (divide by 10 for power, 20 for amplitude)
    gain = 10 ** (config.gain_db / 10.0)

    
    args = ['ffmpeg']
    if config.quiet:
        args += ['-loglevel', 'quiet']
    args += [
        '-f', 'avfoundation',
        '-i', ':2',
        '-f', 's16le',
        '-ac', '1',
        '-ar', f'{config.sample_rate}',
        '-'
    ]
    
    process = subprocess.Popen(args, stdout=subprocess.PIPE, shell=False)
    print(f'mic process started with PID: {process.pid}')

    max_value = (2 ** 16) / 2 - 1
    increment = 1 / max_value
    
    # Buffer for FFT or RMS calculation
    sample_buffer = []
    
    # Track smoothed levels for each band (or single level if not using FFT)
    smoothed_bands = None

    def process_audio(samples):
        """Process audio samples and return levels (FrequencyBands or float)."""
        if config.use_fft and len(samples) >= config.fft_size:
            # Use FFT to get frequency bands
            # Apply Hanning window to reduce spectral leakage
            windowed = samples * np.hanning(len(samples))
            
            # Perform FFT
            fft = np.fft.rfft(windowed)
            magnitudes = np.abs(fft)
            
            # Frequency resolution (Hz per bin)
            freq_resolution = config.sample_rate / len(samples)
            
            # Define frequency band ranges (in Hz)
            # Low: 20-250 Hz, Low-mid: 250-2000 Hz, High-mid: 2000-6000 Hz, High: 6000-20000 Hz
            band_ranges = [
                (20, 250),      # Low (bass)
                (250, 2000),    # Low-mid
                (2000, 6000),   # High-mid
                (6000, 20000)   # High (treble)
            ]
            
            band_levels = []
            for low_freq, high_freq in band_ranges:
                # Convert frequencies to FFT bin indices
                low_bin = int(low_freq / freq_resolution)
                high_bin = int(high_freq / freq_resolution)
                
                # Ensure bins are within valid range
                low_bin = max(0, low_bin)
                high_bin = min(len(magnitudes) - 1, high_bin)
                
                # Calculate RMS for this frequency band
                if high_bin > low_bin:
                    band_rms = np.sqrt(np.mean(magnitudes[low_bin:high_bin] ** 2))
                else:
                    band_rms = 0.0
                
                band_levels.append(band_rms)
            
            # Normalize and apply gain (FFT magnitudes need different scaling)
            # Scale factor accounts for FFT normalization
            scale_factor = 2.0 / len(samples)
            levels = [level * scale_factor * gain for level in band_levels]
            
            return FrequencyBands(*levels)
        else:
            # Simple RMS calculation
            rms = np.sqrt(np.mean(np.array(samples) ** 2))
            return rms * gain

    def apply_processing(levels):
        """Apply compression, smoothing, and clamping to levels."""
        nonlocal smoothed_bands
        
        if isinstance(levels, FrequencyBands):
            # Process each band separately
            processed = []
            for i, level in enumerate(levels):
                # Apply compression
                if config.compression_ratio > 1.0 and level > config.compression_threshold:
                    over = level - config.compression_threshold
                    compressed_over = over / config.compression_ratio
                    level = config.compression_threshold + compressed_over
                
                # Apply smoothing
                if smoothed_bands is None:
                    smoothed_level = level
                else:
                    smoothed_level = config.smoothing * smoothed_bands[i] + (1 - config.smoothing) * level
                
                # Apply thresholding and clamping
                if smoothed_level < config.min_level:
                    smoothed_level = 0.0
                elif smoothed_level > 1.0:
                    smoothed_level = 1.0
                
                processed.append(smoothed_level)
            
            smoothed_bands = processed
            return FrequencyBands(*processed)
        else:
            # Process single level
            level = levels
            
            # Apply compression
            if config.compression_ratio > 1.0 and level > config.compression_threshold:
                over = level - config.compression_threshold
                compressed_over = over / config.compression_ratio
                level = config.compression_threshold + compressed_over
            
            # Apply smoothing
            if smoothed_bands is None:
                smoothed_level = level
            else:
                smoothed_level = config.smoothing * smoothed_bands + (1 - config.smoothing) * level
            
            # Apply thresholding and clamping
            if smoothed_level < config.min_level:
                smoothed_level = 0.0
            elif smoothed_level > 1.0:
                smoothed_level = 1.0
            
            smoothed_bands = smoothed_level
            return smoothed_level

    try:
        while process.poll() is None:
            buffer = process.stdout.read(2)
            
            if buffer:
                # Get the raw sample value (keep signed for proper RMS/FFT)
                raw_value = int.from_bytes(buffer, 'little', signed=True) * increment
                sample_buffer.append(raw_value)
                
                # Process when we have enough samples
                target_size = config.fft_size if config.use_fft else 1
                if len(sample_buffer) >= target_size:
                    samples = np.array(sample_buffer)
                    levels = process_audio(samples)
                    processed_levels = apply_processing(levels)
                    
                    if config.use_fft:
                        print(f'bands - low: {processed_levels.low:.3f}, low_mid: {processed_levels.low_mid:.3f}, '
                              f'high_mid: {processed_levels.high_mid:.3f}, high: {processed_levels.high:.3f}')
                    else:
                        print(f'level: {processed_levels:.5f}')
                    
                    yield processed_levels
                    
                    # For FFT mode, use sliding window (keep last half of samples for overlap)
                    # For RMS mode, clear buffer
                    if config.use_fft:
                        sample_buffer = sample_buffer[len(sample_buffer) // 2:]
                    else:
                        sample_buffer = []
            else:
                print('no more data from ffmpeg, exiting.')
                break

        process.wait()

    except KeyboardInterrupt:
        print('KeyboardInterrupt detected, terminating process...')
        if config.use_fft:
            yield FrequencyBands(0.0, 0.0, 0.0, 0.0)
        else:
            yield 0.0
        process.kill()
        process.wait()

    except Exception as e:
        print(f'Error occurred: {e}')
        process.kill()
        process.wait()

    print('exiting samples_from_mic')

def midi_relay(config: MicSampleConfig) -> None:
    port = mido.open_output(MIDI_DEVICE_NAME, virtual=True)
    try:
        for sample in samples_from_mic(config):
            if isinstance(sample, FrequencyBands):
                # Send each band on a different MIDI control
                port.send(mido.Message('control_change', channel=0, control=1, value=int(sample.low * 127)))
                port.send(mido.Message('control_change', channel=0, control=2, value=int(sample.low_mid * 127)))
                port.send(mido.Message('control_change', channel=0, control=3, value=int(sample.high_mid * 127)))
                port.send(mido.Message('control_change', channel=0, control=4, value=int(sample.high * 127)))
            else:
                # Single value mode
                port.send(mido.Message('control_change', channel=0, control=1, value=int(sample * 127)))
    finally:
        port.close()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='MIDI Relay - run this via cli and select sync from microphone in cli')
    parser.add_argument('--gain', '-g', type=float, default=25.0, help='Gain in decibels (dB). Typical range: 20-60 dB')
    parser.add_argument('--sample-rate', '-sr', type=int, default=44100, help='Sample rate for microphone input (44100 recommended for FFT)')
    parser.add_argument('--fft-size', '-fft', type=int, default=2048, help='FFT window size (power of 2)')
    parser.add_argument('--min-level', '-ml', type=float, default=0.0001, help='Minimum level threshold')
    parser.add_argument('--smoothing', '-s', type=float, default=0.0, help='Exponential smoothing (0.0-1.0): 0=none, 0.5=moderate, 0.9=heavy')
    parser.add_argument('--compression-threshold', '-ct', type=float, default=0.7, help='Compression threshold (0.0-1.0)')
    parser.add_argument('--compression-ratio', '-cr', type=float, default=4.0, help='Compression ratio (1.0=none, 4.0=4:1)')
    parser.add_argument('--use-fft', action='store_true', help='Use FFT for 4-band EQ (default: simple RMS)')

    args = parser.parse_args()

    config = MicSampleConfig(
        gain_db=args.gain,
        sample_rate=args.sample_rate,
        fft_size=args.fft_size,
        min_level=args.min_level,
        smoothing=args.smoothing,
        compression_threshold=args.compression_threshold,
        compression_ratio=args.compression_ratio,
        use_fft=args.use_fft
    )

    midi_relay(config)