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

from concurrent.futures import process
import random
import json
import webbrowser
import time 
import subprocess

from pathlib import Path
from typing import Optional, List, Callable, Set

import mido
import blf
import bpy
import gpu
from gpu_extras.batch import batch_for_shader

from bpy.app.handlers import persistent
from music_player import util
from music_player import config
# from mspec import sample_spec_dir
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

text_scroll_offset_default = 1000
text_scroll_offset = text_scroll_offset_default
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
# midi
#

midi_port:mido.ports.BasePort = None

def redraw_hack():
    # trick to update the GUI
    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

def on_incoming_midi_msg(msg:mido.Message):
    if msg.control == 1:
        value = msg.value / 127
        
        bpy.data.objects['audio signal - full']['signal'] = value
        bpy.data.objects['audio signal - full'].location = (0, 0, 0)

        # bpy.data.objects['audio signal - low']['signal'] = value
        # bpy.data.objects['audio signal - low'].location = (0, 0, 0)

        # bpy.data.objects['audio signal - low mid']['signal'] = value
        # bpy.data.objects['audio signal - low mid'].location = (0, 0, 0)
        
        # bpy.data.objects['audio signal - high mid']['signal'] = value
        # bpy.data.objects['audio signal - high mid'].location = (0, 0, 0)

        # bpy.data.objects['audio signal - high']['signal'] = value
        # bpy.data.objects['audio signal - high'].location = (0, 0, 0)
    
    elif msg.control == 2:
        value = msg.value / 127
        bpy.data.objects['audio signal - low']['signal'] = value
        bpy.data.objects['audio signal - low'].location = (0, 0, 0)
    
    elif msg.control == 3:
        value = msg.value / 127
        bpy.data.objects['audio signal - low mid']['signal'] = value
        bpy.data.objects['audio signal - low mid'].location = (0, 0, 0)

    elif msg.control == 4:
        value = msg.value / 127
        bpy.data.objects['audio signal - high mid']['signal'] = value
        bpy.data.objects['audio signal - high mid'].location = (0, 0, 0)

    elif msg.control == 5:
        value = msg.value / 127
        bpy.data.objects['audio signal - high']['signal'] = value
        bpy.data.objects['audio signal - high'].location = (0, 0, 0)
    
    else:
        print(f'Unhandled MIDI control message: {msg}')

    # update dependecy graph
    

    # bpy.context.view_layer.update()
    # redraw_hack()

#
# visualizer ops
#

# max_value = (2 ** 16) / 2 - 1
# increment = 1 / max_value
# min_level = 0.001
# gain = 175.0

# def handle_microphone_sample():
#     print('handle_microphone_sample()')
#     global ff_mic
#     print(f'ff_mic: {ff_mic}')
#     if ff_mic.poll() is not None:
#         ff_mic = None
#         return None  # process ended, stop the timer. 
#     print('reading microphone input...')
    
#     buffer = ff_mic.stdout.read(2)

#     print(buffer)

#     if buffer:
#         value = (abs(int.from_bytes(buffer, 'little', signed=True)) * increment) * gain
#         if value < min_level:
#             value = 0.0
#         elif value > 1.0:
#             value = 1.0
#         print(f'mic value: {value:.5f}')
#         bpy.data.objects['audio signal - full']['signal'] = value

#     return 0

class MP_OP_sync_to_microphone(bpy.types.Operator):

    bl_idname = 'music_player.sync_to_microphone'
    bl_label = 'Sync to Microphone'
    bl_description = 'Sync the visualizer to the microphone input.'

    def execute(self, context: bpy.types.Context) -> Set[str]:
        bpy.ops.screen.animation_cancel()
        #bpy.ops.screen.animation_play(sync=True)

        global midi_port
        if midi_port is None:
            print('Syncing visualizer to microphone input...')
            midi_port = mido.open_input(util.MIDI_DEVICE_NAME, callback=lambda msg: on_incoming_midi_msg(msg))
        else:
            midi_port.close()
            midi_port = None
            print('Stopped syncing visualizer to microphone input.')

        # graph_area = util.find_area(bpy.context, 'GRAPH_EDITOR')
        # graph_context = util.get_context_for_area(graph_area)

        #bpy.ops.screen.animation_play(sync=True)

        #bpy.app.timers.register(handle_microphone_sample, first_interval=.1, persistent=True)

        # start = time.time()
        # with context.temp_override(**graph_context):
        #     for sample in util.samples_from_mic():
        #         print(sample)
        #         bpy.data.objects['audio signal - full']['signal'] = sample
        #         if time.time() - start > 10.0:
        #             break

        # print('Ending sync to microphone input.')

        return {'FINISHED'}
    

class MP_OP_sync_debug(bpy.types.Operator):
    bl_idname = 'music_player.sync_debug'
    bl_label = 'Sync Debug'
    bl_description = 'Debugging operator to sync visualizer to microphone input.'

    def execute(self, context: bpy.types.Context) -> Set[str]:
        print('Debugging visualizer sync to microphone input...')

        for device in util.list_devices():
            print(f'Available device: {device}')

        print('Default input device:', util.get_default_input())
        return {'FINISHED'}


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
        global app
        context.scene.active_visualizer = 'arctic_wave'

        show_collectons(context, eq=False, wave=True)

        if app is None:
            context.scene.camera = bpy.data.objects['wave cam - main']
        else:
            context.scene.camera = bpy.data.objects['wave cam - side']

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

        if app is None:
            context.scene.camera = bpy.data.objects['wave cam - main']
        else:
            context.scene.camera = bpy.data.objects['wave cam - side']

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

        if app is None:
            context.scene.camera = bpy.data.objects['wave cam - main']
        else:
            context.scene.camera = bpy.data.objects['wave cam - side']

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

first_run_detect_filename_change = True

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
            global first_run_detect_filename_change

            active_filename = bpy.context.active_file.relative_path

            # update globals
            previous_directory = active_directory
            params = bpy.context.area.spaces.active.params
            active_directory = Path(bpy.path.abspath(params.directory.decode('utf-8')))
            previous_filename = active_filename
            
            selected_path = active_directory / active_filename
            ext = selected_path.suffix.lower()

            if first_run_detect_filename_change:
                previous_filename = bpy.context.active_file.relative_path
                first_run_detect_filename_change = False
                print('detect_filename_change() - first run, setting previous_filename:', previous_filename)

            elif ext in ['.wav', '.mp3', '.aac']:
                bpy.ops.music_player.stop()
                print('detect_filename_change() - playing new audio file:', selected_path)
                bpy.ops.music_player.play(sound_path=selected_path.as_posix())
            
            elif ext == '.json':
                print('detect_filename_change() - loading new browser page:', selected_path)
                load_browser_page(selected_path.as_posix())
                for area in bpy.context.screen.areas:
                    if area.type == 'VIEW_3D':
                        area.tag_redraw()
                        break

            else:
                print('detect_filename_change() - not an audio file:', selected_path)
                # bpy.ops.music_player.stop()
                # active_filename = None

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

# documents
# spec_paths = [
#     sample_spec_dir / 'hello-world-page.json',
#     sample_spec_dir / 'test-page.json',
# ]

# state
spec = None
app = None
browser_doc = None
click_boxes = []

def set_browser_page(new_spec:dict) -> None:
    """Set the browser page to the given spec."""
    global spec
    global app
    global browser_doc
    global text_scroll_offset
    global text_scroll_offset_default

    text_scroll_offset = text_scroll_offset_default
    spec = new_spec
    app = lingo_app(new_spec)
    browser_doc = render_output(lingo_update_state(app))

    bpy.ops.music_player.set_arctic_wave()

def load_browser_page(spec_path: str) -> None:
    """Load a browser page from the given spec path."""
    global spec
    global app
    global browser_doc

    with open(spec_path) as f:
        spec = json.load(f)

    set_browser_page(spec)

def unset_browser_page() -> None:
    """Unset the browser page."""
    global spec
    global app
    global browser_doc
    spec = None
    app = None
    browser_doc = None

#load_browser_page(spec_paths[1])

# style
line_height_ratio = 1.75
header_size = 54.0
heading_sizes = {
    1: 54.0,
    2: 45.0,
    3: 40.0,
    4: 36.0,
    5: 30.0,
    6: 24.0
}
text_size = 22.0
left_margin = 100
wrap_width = 750
button_padding = 6
button_background_color = (0.5, 0.5, 0.5, 1.0)
link_color = (0.2, 0.6, 0.8, 1.0)
text_color = (1.0, 1.0, 1.0, 1.0)
button_text_color = (1.0, 1.0, 1.0, 1.0)

blf.size(font_id, text_size)
line_height = blf.dimensions(font_id, 'A')[1] * line_height_ratio

#
# browser ops
#

class MP_TEXT_SCROLL_UP(bpy.types.Operator):

    bl_idname = 'music_player.text_scroll_up'
    bl_label = 'Scroll up'
    bl_description = 'Scroll text up'

    def execute(self, context) -> Set[str]:
        global text_scroll_offset
        text_scroll_offset += text_scroll_increment
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
                break
        # print(f'scrolling up: {text_scroll_offset}')
        return {'FINISHED'}

class MP_TEXT_SCROLL_DOWN(bpy.types.Operator):

    bl_idname = 'music_player.text_scroll_down'
    bl_label = 'Scroll down'
    bl_description = 'Scroll text down'

    def execute(self, context) -> Set[str]:
        global text_scroll_offset
        text_scroll_offset -= text_scroll_increment
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
                break

        # print(f'scrolling down {text_scroll_offset}')
        return {'FINISHED'}
    
class MP_ON_CLICK(bpy.types.Operator):
    """Operator to handle clicks on the browser"""
    bl_idname = 'music_player.on_click'
    bl_label = 'On Click'
    bl_description = 'Handle click events in the browser'

    def invoke(self, context, event) -> Set[str]:
        # This is a placeholder for handling clicks
        # print('MP_ON_CLICK executed')
        # print(context)
        # for name in dir(event):
        #     if not name.startswith('_'):
        #         print(f'{name}: {getattr(event, name)}')
        
        # get screen offset
        mouse_x = event.mouse_x - context.area.x
        mouse_y = event.mouse_y - context.area.y

        # breakpoint() 
        global app
        global browser_doc

        for box in click_boxes:
            # print(f'Click box: {box}')
            if (box['left'] <= mouse_x <= box['right'] and
                box['top'] <= mouse_y <= box['bottom']):
                print(f'\nClicked on {box["type"]} element: {box["element"]}')
                
                if box['type'] == 'button':
                    print(f'\tButton clicked: {box["element"]["text"]}')
                    lingo_execute(app, box['element']['button'])
                    browser_doc = render_output(lingo_update_state(app))
                    for area in context.screen.areas:
                        if area.type == 'VIEW_3D':
                            area.tag_redraw()
                            break
    
                elif box['type'] == 'link':
                    print(f'\tLink clicked: {box["element"]["link"]}')
                    webbrowser.open_new(box['element']['link'])

                return {'FINISHED'}

        print(f'\nEvent type: {event.type}, value: {event.value}, mouse position: ({event.mouse_x}, {event.mouse_y})')
        print(f'\tContext window: {context.window.x}, {context.window.y}, size: {context.window.width}x{context.window.height}')
        print(f'\tArea: type: {context.area.type} x: {context.area.x}, y: {context.area.y}, width: {context.area.width}, height: {context.area.height}')
        print(f'\tRegion: type: {context.region.type} x: {context.region.x}, y: {context.region.y}, size: {context.region.width}x{context.region.height}')
        print(f'\tMouse position (with offset): ({mouse_x}, {mouse_y})')
        
        return {'FINISHED'}

def browser2_debug_drawer(self, context):
    """"""
    document_offset = text_scroll_offset
    text_buffer = ''

    for n, element in enumerate(browser_doc):
        if 'heading' in element:
            blf.size(font_id, heading_sizes[element.get('level', 1)])
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
    global click_boxes
    global app
    global browser_doc

    if app is None:
        return

    click_boxes = []
    document_offset = text_scroll_offset
    left_offset = left_margin
    
    def end_line() -> bool:
        """End current line if we have one, return True if we ended a line."""
        nonlocal document_offset
        nonlocal left_offset
        
        if left_offset > left_margin:
            document_offset -= line_height
            left_offset = left_margin
            return True
        return False

    for n, element in enumerate(browser_doc):
        if 'heading' in element:
            if end_line():
                document_offset -= line_height

            blf.size(font_id, heading_sizes[element.get('level', 1)])
            blf.color(font_id, *text_color)
            blf.position(font_id, left_margin, document_offset, 0)
            blf.draw(font_id, element['heading'])
            document_offset -= line_height * 2

        elif 'link' in element:
            # end_line()
            blf.color(font_id, *link_color)
            try:
                display_text = element["text"]
            except KeyError:
                display_text = element["link"]

            text_dimensions = blf.dimensions(font_id, display_text)

            box = {
                'type': 'link',
                'element': element,
                'left': left_offset,
                'top': document_offset,
                'right': left_offset + text_dimensions[0],
                'bottom': document_offset + text_dimensions[1],
                'hovered': False,
                'clicked': False
            }

            blf.size(font_id, text_size)
            blf.position(font_id, left_offset, document_offset, 0)
            blf.draw(font_id, display_text)
            
            # document_offset -= line_height
            left_offset += text_dimensions[0]
            
            click_boxes.append(box)

        elif 'button' in element:
            end_line()
            blf.size(font_id, text_size)
            blf.color(font_id, *button_text_color)
            blf.position(font_id, left_margin, document_offset, 0)

            # get drawing dimensions of text

            text = element['text']
            dimensions = blf.dimensions(font_id, text)

            box = {
                'type': 'button',
                'element': element,
                'left': left_margin,
                'top': document_offset,
                'right': left_margin + dimensions[0],
                'bottom': document_offset + dimensions[1],
                'hovered': False,
                'clicked': False
            }
            click_boxes.append(box)

            #  create button vertices

            vertices = (
                (box['left'] - button_padding, box['top'] - button_padding), 
                (box['right'] + button_padding, box['top'] - button_padding),
                (box['left'] - button_padding, box['bottom'] + button_padding), 
                (box['right'] + button_padding, box['bottom'] + button_padding)
            )

            indices = (
                (0, 1, 2), (2, 1, 3)
            )

            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
            batch = batch_for_shader(shader, 'TRIS', {'pos': vertices}, indices=indices)

            shader.uniform_float('color', button_background_color)
            batch.draw(shader)


            # draw the button text
            blf.draw(font_id, text)

            document_offset -= line_height

            # print(f'button :: {element["text"]} | left: {left_margin} | top: {document_offset} | right: {left_margin + dimensions[0]} | bottom: {document_offset + dimensions[1]}')
            # print(f'\t{left_margin=} {document_offset=} {dimensions=}')

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
            blf.color(font_id, *text_color)
            blf.position(font_id, left_margin, document_offset, 0)
            blf.draw(font_id, f'input :: {state_field_name} ({field_type})')
            document_offset -= line_height

        elif 'text' in element:
            blf.size(font_id, text_size)
            blf.color(font_id, *text_color)
            blf.position(font_id, left_offset, document_offset, 0)

            text_chunks = element['text'].split(' ')
            last_chunk_index = len(text_chunks) - 1
            for n, chunk in enumerate(text_chunks):
                text_to_draw = chunk + (' ' if n < last_chunk_index else '')
                width = blf.dimensions(font_id, text_to_draw)[0]
                # print(f'chunk :: "{text_to_draw}" | width: {width} | left_offset: {left_offset} | document_offset: {document_offset}')
                if left_offset + width > left_margin + wrap_width:
                    # print(f'wrap  :: {left_offset} + {width} > {left_margin + wrap_width}')
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
    MP_OP_sync_to_microphone,
    MP_OP_sync_debug,
    MP_OP_randomize_visualizer, 
    MP_OP_set_arctic_wave,
    MP_OP_set_broken_radio,
    MP_OP_set_combo_wave,
    MP_OP_set_equalizer,
    MP_OP_play, 
    MP_OP_stop, 
    MP_OT_fullscreen,
    MP_TEXT_SCROLL_UP,
    MP_TEXT_SCROLL_DOWN,
    MP_ON_CLICK
]
load_post_handlers = [init_3d_viewport, init_filebrowser, init_visualizer]
draw_handlers_fb: List[Callable] = []
draw_handlers_spv3d: List[Callable] = []

# ff_mic: Optional[subprocess.Popen] = None
# ff_mic_gain = 175.0
# ff_mic_sample_rate = 30
# ff_mic_min_level = 0.05
# ff_mic_args = [
#     'ffmpeg',
#     '-loglevel', 'quiet',
#     '-f', 'avfoundation',
#     '-i', ':2',
#     '-f', 's16le',
#     '-ac', '1',
#     #'-c:a', 'pcm_u24le', 
#     '-ar', f'{ff_mic_sample_rate}',
#     # '-t', '30', 
#     '-'
# ]

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

    # ffmpeg mic integration
    # global ff_mic
    # ff_mic = subprocess.Popen(ff_mic_args, stdout=subprocess.PIPE, shell=False)
    # print(f'recording process started with PID: {ff_mic.pid}')


def unregister():

    for handler in draw_handlers_spv3d:
        bpy.types.SpaceView3D.draw_handler_remove(handler, 'WINDOW')

    for handler in draw_handlers_fb:
        bpy.types.SpaceFileBrowser.draw_handler_remove(handler, 'WINDOW')

    for handler in load_post_handlers:
        bpy.app.handlers.load_post.remove(handler)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    global midi_port
    if midi_port is not None:
        midi_port.close()