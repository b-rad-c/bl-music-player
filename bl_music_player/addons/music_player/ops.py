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
from typing import Optional, List, Callable, Set

import bpy
import aud

from bpy.app.handlers import persistent
from music_player import opsdata, config


#
# globals
#


# active_media_area: str = 'SEQUENCE_EDITOR'
# active_media_area_obj: bpy.types.Area = None

active_directory: Path = ''
active_filename: Optional[str] = ''
previous_directory: Path = ''
previous_filename: Optional[str] = ''

play_audio: bool = True
audio_device = aud.Device()
audio_handle = None

screen_index: int = 1


def stop_audio():
    global audio_handle
    try:
        audio_handle.stop()
    except AttributeError:
        pass


#
# operators
#


class MP_OP_play(bpy.types.Operator):

    bl_idname = 'music_player.play'
    bl_label = 'Play'
    bl_description = 'Plays a filepath'

    sound_path: bpy.props.StringProperty(name='Sound path', description='The path to a sound file to play')

    def execute(self, context) -> Set[str]:
        print(f'music_player.play({self.sound_path})')

        # reset sequence
        bpy.ops.screen.animation_cancel()
        bpy.context.scene.frame_set(1)
        opsdata.del_all_sequences(context)

        # add audio to sequence
        seq_area = opsdata.find_area(bpy.context, 'SEQUENCE_EDITOR')
        seq_context = opsdata.get_context_for_area(seq_area)
        bpy.ops.sequencer.sound_strip_add(
            seq_context,
            filepath=self.sound_path,
            frame_start=1,
            channel=1
        )
        bpy.ops.sequencer.view_all(seq_context)

        print('\tbaking...')
        graph_area = opsdata.find_area(bpy.context, 'GRAPH_EDITOR')
        graph_context = opsdata.get_context_for_area(graph_area)
        bpy.ops.graph.sound_bake(graph_context, filepath=self.sound_path)

        print('\tplaying...')

        bpy.ops.screen.animation_play(sync=True)
        print('\tdone.')
        return {'FINISHED'}


class MV_OP_screen_cycle(bpy.types.Operator):
    bl_idname = 'music_player.screen_cycle'
    bl_label = 'screen_cycle'
    bl_description = 'screen_cycle'


    def execute(self, context: bpy.types.Context) -> Set[str]:
        global screen_index

        bpy.ops.screen.screen_set(delta=screen_index)
        screen_index *= -1

        init_3d_viewport(None)

        return {'FINISHED'}


class MV_OT_close_filebrowser(bpy.types.Operator):

    bl_idname = 'music_player.close_filebrowser'
    bl_label = 'Close Filebrowser'
    bl_description = 'Close filebrowser area'

    def execute(self, context: bpy.types.Context) -> Set[str]:
        file_browser_area = opsdata.find_area(context, 'FILE_BROWSER')

        if file_browser_area:
            opsdata.close_area(file_browser_area)

        return {'FINISHED'}


class MV_OT_fullscreen(bpy.types.Operator):
    bl_idname = 'music_player.fullscreen'
    bl_label = 'Fullscreen (player)'
    bl_description = 'fullscreen'


    def execute(self, context: bpy.types.Context) -> Set[str]:
        view_3d_area = opsdata.find_area(context, 'VIEW_3D')
        view_3d_context = opsdata.get_context_for_area(view_3d_area)

        with bpy.context.temp_override(**view_3d_context):
            bpy.ops.screen.header_toggle_menus()
            bpy.ops.screen.screen_full_area(use_hide_panels=True)
            bpy.ops.wm.window_fullscreen_toggle()
        
        return {'FINISHED'}
#
# handlers
#

@persistent
def init_3d_viewport(_):
    print('init_3d_viewport()')
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = 'RENDERED'
                    space.show_gizmo = False
                    space.overlay.show_overlays = False

    print('\t-> done')

@persistent
def init_filebrowser(_):
    print('init_filebrowser()')
    params = opsdata.set_filebrowser_directory(config.MUSIC_DIRECTORY)
    params.display_type = 'LIST_VERTICAL'
    print('\t-> done')


@persistent
def callback_filename_change(_):
    # init globals
    global active_directory
    global active_filename
    global previous_directory
    global previous_filename
    global play_audio
    global audio_device
    

    # update globals
    previous_directory = active_directory
    params = bpy.context.area.spaces.active.params
    active_directory = Path(bpy.path.abspath(params.directory.decode('utf-8')))
    previous_filename = active_filename

    # check active file
    if bpy.context.active_file:
        # print('file active')
        active_filename = bpy.context.active_file.relative_path
        if active_filename != previous_filename:
            audio_path = active_directory / active_filename

            if opsdata.is_audio(audio_path):
                # print(f'new audio: {audio_path=}')
                if play_audio:
                    stop_audio()
                    
                    bpy.ops.music_player.play(sound_path=audio_path.as_posix())

    else:
        active_filename = None
        stop_audio()
    



#
# register
#

classes = [MP_OP_play, MV_OT_close_filebrowser, MV_OP_screen_cycle, MV_OT_fullscreen]
load_post_handlers = [init_3d_viewport, init_filebrowser]
draw_handlers_fb: List[Callable] = []


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # Append handlers.
    for handler in load_post_handlers:
        bpy.app.handlers.load_post.append(handler)

    draw_handlers_fb.append(
        bpy.types.SpaceFileBrowser.draw_handler_add(
            callback_filename_change, (None,), 'WINDOW', 'POST_PIXEL'
        )
    )


def unregister():

    # Remove handlers.
    for handler in draw_handlers_fb:
        bpy.types.SpaceFileBrowser.draw_handler_remove(handler, 'WINDOW')

    for handler in load_post_handlers:
        bpy.app.handlers.load_post.remove(handler)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
