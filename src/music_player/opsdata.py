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

from pathlib import Path
from typing import Dict, Optional, Tuple
import bpy
from glob import glob
from music_player.config import VISUALIZER_DIRECTORY


def is_audio(filepath: Path) -> bool:
    return filepath.suffix.lower() in [
        ".wav",
        ".mp3",
        ".aac"
    ]


def find_area(context: bpy.types.Context, area_name: str) -> Optional[bpy.types.Area]:
    if isinstance(context, dict):
        # Handle override context.
        screen = context["screen"]
    else:
        screen = context.screen

    for area in screen.areas:
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


def set_filebrowser_directory(path: Path) -> bpy.types.FileSelectParams:
    area = find_area(bpy.context, 'FILE_BROWSER')
    params = area.spaces.active.params
    params.directory = bytes(path.as_posix(), 'utf-8')
    # print(f'set directory to: {path.as_posix()}')
    return params


def del_all_sequences(context: bpy.types.Context) -> None:
    for seq_name in [s.name for s in context.scene.sequence_editor.sequences_all]:
        context.scene.sequence_editor.sequences.remove(
            context.scene.sequence_editor.sequences[seq_name]
        )


def close_area(area: bpy.types.Area) -> None:
    bpy.ops.screen.area_close(get_context_for_area(area))


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

# 

def load_and_bake_audio(context, sound_path:str, background:bool=False) -> None:

    print(f'music_player.play({sound_path})')

    # reset sequence
    bpy.ops.screen.animation_cancel()
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

    print('\tbaking...')
    graph_area = find_area(bpy.context, 'GRAPH_EDITOR')
    graph_context = get_context_for_area(graph_area)
    with context.temp_override(**graph_context):
        bpy.ops.graph.sound_to_samples(filepath=sound_path)

    # write file

    # bpy.ops.wm.save_as_mainfile(filepath='movie.blend')

    bpy.context.scene.render.filepath = 'movie.mp4' 
    # bpy.context.scene.render.image_settings.file_format = 'PNG'
    