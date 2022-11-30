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
from typing import Optional, List, Callable

import bpy
import aud

from bpy.app.handlers import persistent
from music_player import opsdata, config


#
# globals
#


active_media_area: str = 'SEQUENCE_EDITOR'
active_media_area_obj: bpy.types.Area = None

active_directory: Path = ''
active_filename: Optional[str] = ''
previous_directory: Path = ''
previous_filename: Optional[str] = ''

play_audio: bool = True
audio_device = aud.Device()
audio_handle = None


@persistent
def init_filebrowser(_):
    opsdata.set_filebrowser_directory(config.ASSET_DIRECTORY)


@persistent
def init_active_media_area_obj(_):
    global active_media_area_obj
    global active_media_area
    active_media_area_obj = opsdata.find_area(bpy.context, active_media_area)


@persistent
def callback_filename_change(_):
    # init globals
    global active_directory
    global active_filename
    global previous_directory
    global previous_filename
    global play_audio
    global audio_device
    global audio_handle

    # update globals
    previous_directory = active_directory
    params = bpy.context.area.spaces.active.params
    active_directory = Path(bpy.path.abspath(params.directory.decode('utf-8')))
    previous_filename = active_filename

    # check active file
    if bpy.context.active_file:
        active_filename = bpy.context.active_file.relative_path
        if active_filename != previous_filename:
            audio_path = active_directory / active_filename

            if opsdata.is_audio(audio_path):
                print(f'new audio: {audio_path=}')
                if play_audio:
                    try:
                        # stop current audio if playing
                        audio_handle.stop()
                    except AttributeError:
                        pass

                    sound = aud.Sound(audio_path.as_posix())
                    audio_handle = audio_device.play(sound)
    else:
        active_filename = None
    



# ----------------REGISTER--------------.
classes = []
load_post_handlers = [init_active_media_area_obj, init_filebrowser]
draw_handlers_fb: List[Callable] = []


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # Append handlers.
    for handler in load_post_handlers:
        bpy.app.handlers.load_post.append(handler)

    draw_handlers_fb.append(
        bpy.types.SpaceFileBrowser.draw_handler_add(
            callback_filename_change, (None,), "WINDOW", "POST_PIXEL"
        )
    )


def unregister():

    # Remove handlers.
    for handler in draw_handlers_fb:
        bpy.types.SpaceFileBrowser.draw_handler_remove(handler, "WINDOW")

    for handler in load_post_handlers:
        bpy.app.handlers.load_post.remove(handler)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
