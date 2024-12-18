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

import blf
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

text_scroll_offset = 333
text_scroll_increment = 10

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
        global random_vis_on_play

        print(f'music_player.play({self.sound_path})')

        # reset sequence
        bpy.ops.screen.animation_cancel()
        bpy.context.scene.frame_set(1)
        opsdata.del_all_sequences(context)

        # add audio to sequence
        seq_area = opsdata.find_area(bpy.context, 'SEQUENCE_EDITOR')
        seq_context = opsdata.get_context_for_area(seq_area)
        with context.temp_override(**seq_context):
            bpy.ops.sequencer.sound_strip_add(
                filepath=self.sound_path,
                frame_start=1,
                channel=1
            )

        opsdata.fit_frame_range_to_strips(context)  # seq_context does not have .scene as an attribute?

        with context.temp_override(**seq_context):
            bpy.ops.sequencer.view_all()

        print('\tbaking...')
        graph_area = opsdata.find_area(bpy.context, 'GRAPH_EDITOR')
        graph_context = opsdata.get_context_for_area(graph_area)
        with context.temp_override(**graph_context):
            bpy.ops.graph.sound_to_samples(filepath=self.sound_path)

        if random_vis_on_play:
            print('\trandomizing...')
            bpy.ops.music_player.randomize_visualizer()

        print('\tplaying...')

        bpy.ops.screen.animation_play(sync=True)
        print('\tdone.')

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


class MP_TEXT_SCROLL_UP(bpy.types.Operator):

    bl_idname = 'music_player.text_scroll_up'
    bl_label = 'Scroll up'
    bl_description = 'Scroll text up'

    def execute(self, context) -> Set[str]:
        global text_scroll_offset
        text_scroll_offset += text_scroll_increment
        print(f'scrolling up: {text_scroll_offset}')
        return {'FINISHED'}


class MP_TEXT_SCROLL_DOWN(bpy.types.Operator):

    bl_idname = 'music_player.text_scroll_down'
    bl_label = 'Scroll down'
    bl_description = 'Scroll text down'

    def execute(self, context) -> Set[str]:
        global text_scroll_offset
        text_scroll_offset -= text_scroll_increment
        print(f'scrolling down {text_scroll_offset}')
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


def text_overlay_drawer(self, context):
    global text_scroll_offset
    font_id = 0
    # currently scroll is only responsive if song is playing
    blf.size(font_id, 54.0)
    blf.position(font_id, 100, 1000 + text_scroll_offset, 0)
    blf.draw(font_id, 'Test Header')

    blf.size(font_id, 42.0)
    blf.position(font_id, 100, 925 + text_scroll_offset, 0)
    blf.draw(font_id, 'hello.world')


#
# register
#

classes = [MP_OP_randomize_visualizer, MP_OP_play, MP_OP_stop, MV_OT_fullscreen, MP_TEXT_SCROLL_UP, MP_TEXT_SCROLL_DOWN]
load_post_handlers = [init_3d_viewport, init_filebrowser]
draw_handlers_fb: List[Callable] = []
draw_handlers_spv3d: List[Callable] = []

def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    for handler in load_post_handlers:
        bpy.app.handlers.load_post.append(handler)

    draw_handlers_fb.append(
        bpy.types.SpaceFileBrowser.draw_handler_add(callback_filename_change, (None,), 'WINDOW', 'POST_PIXEL')
    )

    draw_handlers_spv3d.append(
        bpy.types.SpaceView3D.draw_handler_add(text_overlay_drawer, (None, None), 'WINDOW', 'POST_PIXEL')
    )


def unregister():

    for handler in draw_handlers_spv3d:
        bpy.types.SpaceView3D.draw_handler_remove(handler, 'WINDOW')

    for handler in draw_handlers_fb:
        bpy.types.SpaceFileBrowser.draw_handler_remove(handler, 'WINDOW')

    for handler in load_post_handlers:
        bpy.app.handlers.load_post.remove(handler)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
