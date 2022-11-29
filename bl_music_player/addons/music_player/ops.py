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
from typing import Set, Optional, List, Callable
from collections import OrderedDict
from copy import copy

import bpy
from bpy.app.handlers import persistent

from music_player import opsdata, config

logger = config.LoggerFactory.getLogger(name=__name__)

# Global variables
active_media_area: str = "SEQUENCE_EDITOR"
active_media_area_obj: bpy.types.Area = None  # Is initialized by init_active_media_area_obj()  # TODO: replace finding active media area with this global area obj
force_update_media = False

# Global variables for frame handler to check previous value.
prev_dirpath: Path = Path.home()  # TODO: read from json on register
prev_relpath: Optional[str] = None
prev_filepath_list: List[Path] = []

#active_dirpath: Path = Path.home()
#active_relpath: Optional[str] = None
active_dirpath: Path = '/Users/brad/Pictures/Toby'
active_relpath: Optional[str] = 'IMG_2290.JPG'
active_filepath_list: List[Path] = []

last_folder_at_path: OrderedDict = OrderedDict()
active_bookmark_group_name: str = ""


def get_active_path() -> Path:
    global active_dirpath
    global active_relpath
    return Path(active_dirpath).joinpath(active_relpath)


class MV_OT_load_media_image(bpy.types.Operator):

    bl_idname = "media_viewer.load_media_image"
    bl_label = "Load Image"
    bl_description = (
        "Loads image media in to image editor and clears any media before that"
    )
    filepath: bpy.props.StringProperty(name="Filepath", subtype="FILE_PATH")

    playback: bpy.props.BoolProperty(
        name="Playback",
        description="Controls if image sequence should playback after load",
        default=True,
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def execute(self, context: bpy.types.Context) -> Set[str]:
        print('media_viewer.load_media_image()')
        filepath = Path(self.filepath)

        # Stop playback.
        bpy.ops.screen.animation_cancel()

        # Check if filepath exists.
        if not filepath.exists():
            return {"CANCELLED"}

        # Check if image editor area available.
        area = opsdata.find_area(context, "IMAGE_EDITOR")
        if not area:
            logger.error("Failed to load image media. No Image Editor area available.")
            return {"CANCELLED"}

        file_list = [filepath]

        # Create new image datablock.
        image = bpy.data.images.load(file_list[0].as_posix(), check_existing=True)
        image.name = filepath.stem

        # Set active image.
        area.spaces.active.image = image

        # Fit view, has to be done before setting sequence, otherwise
        # image won't resize? Weird.
        opsdata.fit_image_editor_view(context, area=area)

        # Set frame range to 1.
        context.scene.frame_start = 1
        context.scene.frame_end = 1
        context.scene.frame_current = 1

        # Fit timeline view.
        #opsdata.fit_timeline_view(context)

        # Set scene resolution.
        context.scene.render.resolution_x = int(image.resolution[0])
        context.scene.render.resolution_y = int(image.resolution[1])

        # Set colorspace depending on file extension:
        if file_list[0].suffix == ".exr":
            context.scene.view_settings.view_transform = "Filmic"
            image.use_view_as_render = True
        else:
            context.scene.view_settings.view_transform = "Standard"
            image.use_view_as_render = False

        return {"FINISHED"}


class MV_OT_set_media_area_type(bpy.types.Operator):

    bl_idname = "media_viewer.set_media_area_type"
    bl_label = "Set media area type"
    bl_description = "Sets media are type to specified area type"

    area_type: bpy.props.StringProperty(
        name="Area Type",
        description="Type that media area should be changed to",
        default="SEQUENCE_EDITOR",
    )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        print('media_viewer.set_media_area_type()')
        global active_media_area
        global active_media_area_obj

        # Find active media area.
        area_media = opsdata.find_area(context, active_media_area)

        if not area_media:
            logger.info(
                f"Failed to find active media area of type: {active_media_area}"
            )
            return {"CANCELLED"}

        # Early return if same type already.
        if area_media.type == self.area_type:
            return {"FINISHED"}

        # Change area type.
        area_media.type = self.area_type

        # Update global media area type.
        active_media_area = area_media.type
        active_media_area_obj = area_media

        # Set annotate tool as active.
        if area_media.type in ["SEQUENCE_EDITOR", "IMAGE_EDITOR"]:
            bpy.ops.wm.tool_set_by_id({"area": area_media}, name="builtin.annotate")

        logger.info(f"Changed active media area to: {area_media.type}")

        return {"FINISHED"}


@persistent
def init_active_media_area_obj(dummy: None):
    global active_media_area_obj
    global active_media_area
    active_media_area_obj = opsdata.find_area(bpy.context, active_media_area)


@persistent
def callback_filename_change(dummy: None):
    """
    This will be registered as a draw handler on the filebrowser and runs everytime the
    area gets redrawn. This handles the dynamic loading of the selected media and
    saves filebrowser directory on window manager to restore it on area toggling.
    """
    # Read only.
    global last_folder_at_path  # :List[Path]

    # Will be overwritten.
    global active_relpath  # :Optional[str]
    global active_dirpath  # :Path
    global active_filepath_list  # :List[Path]
    global prev_relpath  # :Optional[str]
    global prev_dirpath  # :Path
    global prev_filepath_list  # :List[Path]
    global force_update_media  # :bool

    # Because frame handler runs in area,
    # context has active_file, and selected_files.
    area = bpy.context.area
    active_file = bpy.context.active_file  # Can be None.
    selected_files = bpy.context.selected_files
    params = area.spaces.active.params
    directory = Path(bpy.path.abspath(params.directory.decode("utf-8")))

    # Update globals.
    active_dirpath = directory
    active_relpath = active_file.relative_path if active_file else None
    #print('active_dirpath:', active_dirpath)
    #print('active_relpath:', active_relpath)

    # Save recent directory to config file if direcotry changed.
    # Save and load from folder history.
    if prev_dirpath != active_dirpath:

        # Save recent_dir to config file on disk, to restore it on next
        # startup.
        config.save_config({"recent_dir": active_dirpath.as_posix()})
        logger.info(f"Saved new recent directory: {active_dirpath.as_posix()}")

        # Check if current directory has an entry in folder history.
        # If so select that folder.
        if active_dirpath.as_posix() in last_folder_at_path:
            area.spaces.active.activate_file_by_relative_path(
                relative_path=last_folder_at_path[active_dirpath.as_posix()]
            )

        # Update global var prev_dirpath with current directory.
        prev_dirpath = active_dirpath

    # Early return no active_file:
    if not active_file:
        return

    # When user goes in fullscreen mode and then exits, selected_files will be None
    # And therefore media files will be cleared. Active file tough survives the full
    # screen mode switch. Therefore we can append that to selected files, so we don't
    # loose the loaded media.
    if not selected_files:
        selected_files.append(active_file)

    # Update global active filepath list.
    active_filepath_list.clear()
    active_filepath_list.extend(
        [directory.joinpath(Path(file.relative_path)) for file in selected_files]
    )
    active_filepath = get_active_path()

    if opsdata.is_image(active_filepath):

        # Early return filename did not change.
        if prev_relpath == active_relpath:
            if force_update_media:
                force_update_media = False
            else:
                return None

        # Set area type.
        bpy.ops.media_viewer.set_media_area_type(area_type="IMAGE_EDITOR")

        # Load media image handles image sequences.
        bpy.ops.media_viewer.load_media_image(filepath=active_filepath.as_posix())

    # Update prev_ variables.
    prev_relpath = active_relpath
    prev_filepath_list.clear()
    prev_filepath_list.extend(copy(active_filepath_list))


# ----------------REGISTER--------------.
classes = [
    MV_OT_load_media_image,
    MV_OT_set_media_area_type
]
draw_handlers_fb: List[Callable] = []


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # Append handlers.
    bpy.app.handlers.load_post.append(init_active_media_area_obj)
    draw_handlers_fb.append(
        bpy.types.SpaceFileBrowser.draw_handler_add(
            callback_filename_change, (None,), "WINDOW", "POST_PIXEL"
        )
    )


def unregister():

    # Remove handlers.
    for handler in draw_handlers_fb:
        bpy.types.SpaceFileBrowser.draw_handler_remove(handler, "WINDOW")

    bpy.app.handlers.load_post.remove(init_active_media_area_obj)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
