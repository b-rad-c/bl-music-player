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
from random import randint

import bpy

from bpy.app.handlers import persistent
from music_player import opsdata, config



#
# globals
#


active_directory: Path = ''
active_filename: Optional[str] = ''
previous_directory: Path = ''
previous_filename: Optional[str] = ''

play_audio = True
screen_index = 1
random_vis_on_play = True
is_fullscreen = False
is_reverting_fullscreen = False

active_file = None

#
# operators
#


@persistent
def randomize_vis():
    print('\trandomize_vis()')

    waveform = bpy.context.active_object
    waveform['color_preset'] = randint(0, 3)

    nodes = waveform.modifiers['GeometryNodes']
    nodes['Input_2'] = bool(randint(0, 1))
    nodes['Input_3'] = bool(randint(0, 1))

    # bpy.context.scene.update_render_engine()
    # bpy.context.scene.update_tag()
    bpy.context.view_layer.update()


class MP_OP_randomize_visualizer(bpy.types.Operator):

    bl_idname = 'music_player.randomize_visualizer'
    bl_label = 'Randomize visualizer'
    bl_description = 'Sets random values for the visualizer parameters'

    def execute(self, context) -> Set[str]:
        waveform = context.active_object
        waveform['color_preset'] = randint(0, 3)

        nodes = waveform.modifiers['GeometryNodes']
        nodes['Input_2'] = bool(randint(0, 1))
        nodes['Input_3'] = bool(randint(0, 1))

        # bpy.context.scene.update_render_engine()
        # bpy.context.scene.update_tag()
        context.view_layer.update()
        return {'FINISHED'}


class MP_OP_play(bpy.types.Operator):

    bl_idname = 'music_player.play'
    bl_label = 'Play'
    bl_description = 'Plays a filepath'

    sound_path: bpy.props.StringProperty(name='Sound path', description='The path to a sound file to play')

    def execute(self, context) -> Set[str]:
        opsdata.load_and_bake_audio(context, sound_path=self.sound_path)

        bpy.ops.screen.animation_play(sync=True)

        return {'FINISHED'}


class MP_OP_stop(bpy.types.Operator):

    bl_idname = 'music_player.stop'
    bl_label = 'Stop'
    bl_description = 'Stop playing the current audio.'

    def execute(self, context: bpy.types.Context) -> Set[str]:
        bpy.ops.screen.animation_cancel()
        return {'FINISHED'}


class MV_OT_fullscreen(bpy.types.Operator):
    bl_idname = 'music_player.fullscreen'
    bl_label = 'Fullscreen + Fill Area'
    bl_description = 'fullscreen'

    def execute(self, context: bpy.types.Context) -> Set[str]:
        global is_fullscreen
        global is_reverting_fullscreen

        print(f'music_player.fullscreen {is_fullscreen=} {is_reverting_fullscreen=}')

        view_3d_area = opsdata.find_area(bpy.context, 'VIEW_3D')
        view_3d_context = bpy.context.copy()
        view_3d_context['area'] = view_3d_area

        with context.temp_override(**view_3d_context):
            if is_reverting_fullscreen:
                # for some reason this operator runs multiple times when called?
                # use this global to ensure only the first instance runs to prevent race conditions
                print('music_player.fullscreen_test - cancel')
                return {'CANCELLED'}
            elif is_fullscreen:
                is_reverting_fullscreen = True
                print('music_player.fullscreen_test - revert')
                bpy.ops.screen.header_toggle_menus()
                bpy.ops.screen.back_to_previous()
                bpy.ops.wm.window_fullscreen_toggle()
                is_reverting_fullscreen = False
            else:
                print('music_player.fullscreen_test - enable')
                bpy.ops.screen.header_toggle_menus()
                bpy.ops.screen.screen_full_area(use_hide_panels=True)
                bpy.ops.wm.window_fullscreen_toggle()

        is_fullscreen = not is_fullscreen
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
    global is_reverting_fullscreen

    # update globals
    previous_directory = active_directory
    params = bpy.context.area.spaces.active.params
    active_directory = Path(bpy.path.abspath(params.directory.decode('utf-8')))
    previous_filename = active_filename

    # check active file
    if bpy.context.active_file and not is_reverting_fullscreen:
        active_filename = bpy.context.active_file.relative_path
        if active_filename != previous_filename:
            audio_path = active_directory / active_filename

            if opsdata.is_audio(audio_path):
                if play_audio:
                    bpy.ops.music_player.stop()
                    bpy.ops.music_player.play(sound_path=audio_path.as_posix())

    else:
        active_filename = None
        bpy.ops.music_player.stop()
    

#
# register
#

classes = [MP_OP_randomize_visualizer, MP_OP_play, MP_OP_stop, MV_OT_fullscreen]
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
