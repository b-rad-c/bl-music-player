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

import random
import json
from pathlib import Path
from typing import Optional, List, Callable, Set

import blf
import bpy

from bpy.app.handlers import persistent
from music_player import util, config
from mspec import sample_spec_dir
from mspec.markup import lingo_app, render_output, lingo_execute, lingo_update_state



#
# globals
#

active_directory: Path = ''
active_filename: Optional[str] = ''
previous_directory: Path = ''
previous_filename: Optional[str] = ''

screen_index = 1
random_vis_on_play = True
is_fullscreen = False
changing_fullscreen = False

active_file = None

text_scroll_offset = 1000
text_scroll_increment = 50
visualizers = [
    {'id': 'arctic_wave', 'label': 'Arctic Wave'},
    {'id': 'broken_radio', 'label': 'Broken Radio'},
    {'id': 'combo_wave', 'label': 'Combo Wave'},
    {'id': 'equalizer', 'label': 'Equalizer'}
]

default_visualizer = visualizers[0]['id']

bpy.types.Scene.active_visualizer = bpy.props.StringProperty(name='active_visualizer', 
                                                             default=default_visualizer,
                                                             description='The currently active visualizer')

def show_collectons(context: bpy.types.Context, eq: bool = False, wave: bool = True) -> None:
    """
    Show or hide the collections based on the visualizer.
    :param context: The Blender context.
    :param eq: Whether to show the equalizer collection.
    :param wave: Whether to show the wave collection.
    """
    context.layer_collection.children['eq'].hide_viewport = not eq
    context.layer_collection.children['eq'].collection.hide_render = not eq

    context.layer_collection.children['wave'].hide_viewport = not wave
    context.layer_collection.children['wave'].collection.hide_render = not wave

def dump(context, full=False):
    for attr in dir(context):
        value = getattr(context, attr)

        try:
            for key, val in value.children.items():
                print(f'{attr}.{key} >>> {val}')
        except (TypeError, AttributeError):
            try:
                for key, val in value.items():
                    print(f'{attr}.{key} >>> {val}')
            except (TypeError, AttributeError):
                if isinstance(value, list):
                    for item in value:
                        print(f'{attr} >>> {item}')
                else:
                    print(f'{attr} = {getattr(context, attr)}')

#
# visualizer ops
#

class MP_OP_randomize_visualizer(bpy.types.Operator):

    bl_idname = 'music_player.randomize_visualizer'
    bl_label = 'Randomize visualizer'
    bl_description = 'Sets random values for the visualizer parameters'

    def execute(self, context) -> Set[str]:
        global visualizers

        while True:
            visualizer = random.choice(visualizers)
            if visualizer['id'] != context.scene.active_visualizer:
                break
        
        try:
            getattr(bpy.ops.music_player, f'set_{visualizer["id"]}')()
        except AttributeError as e:
            print(f'Error randomizing visualizer | AttributeError: {e}')
            return {'CANCELLED'}

        return {'FINISHED'}
    

class MP_OP_set_arctic_wave(bpy.types.Operator):

    bl_idname = 'music_player.set_arctic_wave'
    bl_label = 'Set Arctic Wave visualizer'
    bl_description = 'Changes the visualizer to Arctic Wave'

    def execute(self, context) -> Set[str]:
        context.scene.active_visualizer = 'arctic_wave'

        show_collectons(context, eq=False, wave=True)

        context.scene.camera = bpy.data.objects['Camera']

        # bpy.data.collections['wave'].hide_viewport = False
        # bpy.data.collections['wave'].hide_render = False

        context.scene.objects['wave 1'].hide_viewport = False
        context.scene.objects['wave 1'].hide_render = False

        context.scene.objects['wave 2'].hide_viewport = True
        context.scene.objects['wave 2'].hide_render = True

        return {'FINISHED'}
    

class MP_OP_set_broken_radio(bpy.types.Operator):
    bl_idname = 'music_player.set_broken_radio'
    bl_label = 'Set Broken Radio visualizer'
    bl_description = 'Changes the visualizer to Broken Radio'

    def execute(self, context) -> Set[str]:
        context.scene.active_visualizer = 'broken_radio'

        show_collectons(context, eq=False, wave=True)

        context.scene.camera = bpy.data.objects['Camera']

        context.scene.objects['wave 1'].hide_viewport = True
        context.scene.objects['wave 1'].hide_render = True

        context.scene.objects['wave 2'].hide_viewport = False
        context.scene.objects['wave 2'].hide_render = False

        return {'FINISHED'}
    

class MP_OP_set_combo_wave(bpy.types.Operator):
    bl_idname = 'music_player.set_combo_wave'
    bl_label = 'Set Combo Wave visualizer'
    bl_description = 'Changes the visualizer to Combo Wave'

    def execute(self, context) -> Set[str]:
        context.scene.active_visualizer = 'combo_wave'

        show_collectons(context, eq=False, wave=True)

        context.scene.camera = bpy.data.objects['Camera']

        context.scene.objects['wave 1'].hide_viewport = False
        context.scene.objects['wave 1'].hide_render = False

        context.scene.objects['wave 2'].hide_viewport = False
        context.scene.objects['wave 2'].hide_render = False

        return {'FINISHED'}
    

class MP_OP_set_equalizer(bpy.types.Operator):

    bl_idname = 'music_player.set_equalizer'
    bl_label = 'Set Equalizer visualizer'
    bl_description = 'Changes the visualizer to Equalizer'

    def execute(self, context) -> Set[str]:
        context.scene.active_visualizer = 'equalizer'
        
        show_collectons(context, eq=True, wave=False)

        eq_cam_names = list(filter(lambda c: c.startswith('eq cam'), bpy.data.objects.keys()))
        eq_cam_names.sort()
        
        context.scene.camera = bpy.data.objects[eq_cam_names[0]]

        print(f'camera names: {eq_cam_names}')

        def change_camera():
            if context.scene.active_visualizer != 'equalizer':
                # return None to disable the timer
                print('change_camera() - visualizer changed, disabling timer')
                return None
            
            new_cam = random.choice(eq_cam_names)
            context.scene.camera = bpy.data.objects[new_cam]

            delay = random.uniform(5, 10)  # random delay between 5 and 15 seconds
            print(f'change_camera() - changing camera to {new_cam}, next change in {delay:.2f} seconds')

            return delay  # return a random time in seconds to change the camera again
        
        bpy.app.timers.register(change_camera, first_interval=10, persistent=True)

        return {'FINISHED'}
    

#
# playback ops
#

class MP_OP_play(bpy.types.Operator):

    bl_idname = 'music_player.play'
    bl_label = 'Play'
    bl_description = 'Plays a filepath'

    sound_path: bpy.props.StringProperty(name='Sound path', description='The path to a sound file to play')

    def execute(self, context) -> Set[str]:
        util.load_and_bake_audio(context, sound_path=self.sound_path)

        bpy.ops.screen.animation_play(sync=True)

        return {'FINISHED'}


class MP_OP_stop(bpy.types.Operator):

    bl_idname = 'music_player.stop'
    bl_label = 'Stop'
    bl_description = 'Stop playing the current audio.'

    def execute(self, context: bpy.types.Context) -> Set[str]:
        bpy.ops.screen.animation_cancel()
        return {'FINISHED'}


class MP_OT_fullscreen(bpy.types.Operator):
    bl_idname = 'music_player.fullscreen'
    bl_label = 'Fullscreen + Fill Area'
    bl_description = 'fullscreen'

    def execute(self, context: bpy.types.Context) -> Set[str]:
        global is_fullscreen
        global changing_fullscreen

        print(f'* music_player.fullscreen {is_fullscreen=} {changing_fullscreen=}')

        view_3d_area = util.find_area(context, 'VIEW_3D')
        view_3d_context = util.get_context_for_area(view_3d_area)

        with context.temp_override(**view_3d_context):
            if changing_fullscreen:
                # for some reason this operator runs multiple times when called?
                # use this global to ensure only the first instance runs to prevent race conditions
                print('music_player.fullscreen_test - cancel')
                return {'CANCELLED'}
            
            elif is_fullscreen:
                changing_fullscreen = True
                print('music_player.fullscreen_test - revert')
                
                bpy.ops.screen.back_to_previous()
                bpy.ops.screen.header_toggle_menus()
                bpy.ops.wm.window_fullscreen_toggle()
                changing_fullscreen = False
                is_fullscreen = False
                return {'FINISHED'}

            else:
                changing_fullscreen = True
                print('music_player.fullscreen_test - enable')
                bpy.ops.screen.header_toggle_menus()
                bpy.ops.screen.screen_full_area(use_hide_panels=True)
                bpy.ops.wm.window_fullscreen_toggle()
                changing_fullscreen = False
                is_fullscreen = True
                return {'FINISHED'}


class MP_TEXT_SCROLL_UP(bpy.types.Operator):

    bl_idname = 'music_player.text_scroll_up'
    bl_label = 'Scroll up'
    bl_description = 'Scroll text up'

    def execute(self, context) -> Set[str]:
        global text_scroll_offset
        text_scroll_offset += text_scroll_increment
        for area in context.screen.areas:
            area.tag_redraw()
        print(f'scrolling up: {text_scroll_offset}')
        return {'FINISHED'}


class MP_TEXT_SCROLL_DOWN(bpy.types.Operator):

    bl_idname = 'music_player.text_scroll_down'
    bl_label = 'Scroll down'
    bl_description = 'Scroll text down'

    def execute(self, context) -> Set[str]:
        global text_scroll_offset
        text_scroll_offset -= text_scroll_increment
        for area in context.screen.areas:
            area.tag_redraw()
        
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
def init_visualizer(_):

    visualizer = bpy.context.scene.active_visualizer

    print('init_visualizer() - ', visualizer)

    try:
        getattr(bpy.ops.music_player, f'set_{visualizer}')()
    except AttributeError as e:
        print(f'Error initializing visualizer | AttributeError: {e}')
        return {'CANCELLED'}

    print('\t-> done')

@persistent
def init_filebrowser(_):
    print('init_filebrowser()')
    #params = util.set_filebrowser_directory()


    area = util.find_area(bpy.context, 'FILE_BROWSER')
    params = area.spaces.active.params
    params.directory = bytes(config.MUSIC_DIRECTORY.as_posix(), 'utf-8')
    params.display_type = 'LIST_VERTICAL'

    # file_browser_context = util.get_context_for_area(area)
    # with bpy.context.temp_override(**file_browser_context):
    #     # dump(bpy.context, full=True)
    #     fb = bpy.context.space_data
    #     # fb.params.filename
    #     #breakpoint()
    #     bpy.msgbus.subscribe_rna(
    #         key=fb.params,
    #         owner=music_player_owner,
    #         args=(),
    #         notify=active_file_changed,
    #         options={'PERSISTENT'}
    #     )
    #     print(f'subscribed to active_file changes: {fb}')
    print('\t-> done')

@persistent
def detect_filename_change(_):
    """this is run each time the filebrowser is redrawn, so we can check if the active file has changed"""

    global changing_fullscreen

    # if we are in filebrowser
    if bpy.context.active_file and not changing_fullscreen:
        global previous_filename

        # if filename has changed update state and play audio
        if previous_filename != bpy.context.active_file.relative_path:
            global active_filename
            global active_directory
            global previous_directory

            active_filename = bpy.context.active_file.relative_path

            # update globals
            previous_directory = active_directory
            params = bpy.context.area.spaces.active.params
            active_directory = Path(bpy.path.abspath(params.directory.decode('utf-8')))
            previous_filename = active_filename
            
            audio_path = active_directory / active_filename

            if audio_path.suffix.lower() in ['.wav', '.mp3', '.aac']:
                bpy.ops.music_player.stop()
                bpy.ops.music_player.play(sound_path=audio_path.as_posix())

    else:
        print('detect_filename_change() - not active file or reverting fullscreen')
        # active_filename = None
        # bpy.ops.music_player.stop()


#
# browser 2
#

font_id = 0

# ui_scale = context.preferences.view.ui_scale
# blf.enable(0, blf.WORD_WRAP)
# blf.word_wrap(0, 500)
blf.color(font_id, 1.0, 1.0, 1.0, 1.0)

# documents
spec_paths = [
    sample_spec_dir / 'hello-world-page.json',
    sample_spec_dir / 'test-page.json',
]
def load_page(spec_path: str) -> dict:
    with open(spec_path) as f:
        return json.load(f)

# state
spec = load_page(spec_paths[1])
app = lingo_app(spec)
browser_doc = render_output(lingo_update_state(app))

# style
line_height_ratio = 1.75
header_size = 54.0
text_size = 22.0
left_margin = 100
wrap_width = 750

blf.size(font_id, text_size)
line_height = blf.dimensions(font_id, 'A')[1] * line_height_ratio


def browser2_debug_drawer(self, context):
    """"""
    document_offset = text_scroll_offset
    text_buffer = ''

    for n, element in enumerate(browser_doc):
        if 'heading' in element:
            blf.size(font_id, header_size)
            blf.position(font_id, left_margin, document_offset, 0)
            blf.draw(font_id, element['heading'])
            document_offset -= line_height

        elif 'link' in element:
            try:
                display_text = element['text']
            except KeyError:
                display_text = element['link']
            
            blf.size(font_id, text_size)
            blf.position(font_id, left_margin, document_offset, 0)
            blf.draw(font_id, f'link :: {display_text} ({element["link"]})')
            document_offset -= line_height

        elif 'button' in element:
            blf.size(font_id, text_size)
            blf.position(font_id, left_margin, document_offset, 0)
            blf.draw(font_id, 'button :: ' + element['text'])
            document_offset -= line_height

        elif 'break' in element:
            blf.size(font_id, text_size)
            blf.position(font_id, left_margin, document_offset, 0)
            blf.draw(font_id, f'break :: {element["break"]}')
            document_offset -= line_height * element['break']

        elif 'input' in element:
            
            try:
                state_field_name = list(element['bind']['state'].keys())[0]
            except (KeyError, IndexError):
                raise ValueError('Input element must bind to a state state')
            
            field_type = app.spec['state'][state_field_name]['type']
            
            blf.size(font_id, text_size)
            blf.position(font_id, left_margin, document_offset, 0)
            blf.draw(font_id, f'input :: {state_field_name} ({field_type})')
            document_offset -= line_height

        elif 'text' in element:
            blf.size(font_id, text_size)
            blf.position(font_id, left_margin, document_offset, 0)
            blf.draw(font_id, f'text :: {element["text"]}')
            text_buffer += element['text']
            document_offset -= line_height

        else:
            raise ValueError('Unknown element type')


def browser2_drawer(self, context):
    """"""
    document_offset = text_scroll_offset
    left_offset = left_margin
    
    def end_line():
        nonlocal document_offset
        nonlocal left_offset
        
        if left_offset > left_margin:
            document_offset -= line_height
            left_offset = left_margin

    for n, element in enumerate(browser_doc):
        if 'heading' in element:
            end_line()
            blf.size(font_id, header_size)
            blf.position(font_id, left_margin, document_offset, 0)
            blf.draw(font_id, element['heading'])
            document_offset -= line_height * 2

        elif 'link' in element:
            # end_line()
            try:
                display_text = f'<{element["text"]}>'
            except KeyError:
                display_text = f'<{element["link"]}>'
            
            blf.size(font_id, text_size)
            blf.position(font_id, left_offset, document_offset, 0)
            blf.draw(font_id, display_text)
            left_offset += blf.dimensions(font_id, display_text)[0]
            # document_offset -= line_height

        elif 'button' in element:
            end_line()
            blf.size(font_id, text_size)
            blf.position(font_id, left_margin, document_offset, 0)
            blf.draw(font_id, 'button :: ' + element['text'])
            document_offset -= line_height

        elif 'break' in element:
            # don't use end_line bc it may insert a break
            # end_line()
            document_offset -= line_height * element['break']
            left_offset = left_margin

        elif 'input' in element:
            end_line()
            try:
                state_field_name = list(element['bind']['state'].keys())[0]
            except (KeyError, IndexError):
                raise ValueError('Input element must bind to a state state')
            
            field_type = app.spec['state'][state_field_name]['type']
            
            blf.size(font_id, text_size)
            blf.position(font_id, left_margin, document_offset, 0)
            blf.draw(font_id, f'input :: {state_field_name} ({field_type})')
            document_offset -= line_height

        elif 'text' in element:
            blf.size(font_id, text_size)
            blf.position(font_id, left_offset, document_offset, 0)

            text_chunks = element['text'].split(' ')
            last_chunk_index = len(text_chunks) - 1
            for n, chunk in enumerate(text_chunks):
                text_to_draw = chunk + (' ' if n < last_chunk_index else '')
                width = blf.dimensions(font_id, text_to_draw)[0]
                print(f'chunk :: "{text_to_draw}" | width: {width} | left_offset: {left_offset} | document_offset: {document_offset}')
                if left_offset + width > left_margin + wrap_width:
                    print(f'wrap  :: {left_offset} + {width} > {left_margin + wrap_width}')
                    end_line()
                
                blf.position(font_id, left_offset, document_offset, 0)

                blf.draw(font_id, text_to_draw)
                left_offset += width

        else:
            raise ValueError('Unknown element type')
        
    end_line()

#
# register
#

load_post_handlers = [init_3d_viewport, init_filebrowser]
classes = [
    MP_OP_randomize_visualizer, 
    MP_OP_set_arctic_wave,
    MP_OP_set_broken_radio,
    MP_OP_set_combo_wave,
    MP_OP_set_equalizer,
    MP_OP_play, 
    MP_OP_stop, 
    MP_OT_fullscreen,
    MP_TEXT_SCROLL_UP,
    MP_TEXT_SCROLL_DOWN
]
load_post_handlers = [init_3d_viewport, init_filebrowser, init_visualizer]
draw_handlers_fb: List[Callable] = []
draw_handlers_spv3d: List[Callable] = []

def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    for handler in load_post_handlers:
        bpy.app.handlers.load_post.append(handler)

    draw_handlers_fb.append(
        bpy.types.SpaceFileBrowser.draw_handler_add(detect_filename_change, (None,), 'WINDOW', 'POST_PIXEL')
    )

    draw_handlers_spv3d.append(
        bpy.types.SpaceView3D.draw_handler_add(browser2_drawer, (None, None), 'WINDOW', 'POST_PIXEL')
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

    # bpy.msgbus.clear_by_owner(music_player_owner)