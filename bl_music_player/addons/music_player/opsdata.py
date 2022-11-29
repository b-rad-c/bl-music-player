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
from typing import Dict, Optional

import bpy

from music_player import config

# MEDIA VIEWER

logger = config.LoggerFactory.getLogger(name=__name__)


def is_image(filepath: Path) -> bool:
    EXT_IMG = [
        ".jpg",
        ".png",
        ".exr",
        ".jpeg",
        ".tif",
        ".tiff",
        ".psd"
    ]
    if filepath.suffix.lower() in EXT_IMG:
        return True
    return False


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


def fit_image_editor_view(
    context: bpy.types.Context, area: bpy.types.Area = None
) -> None:
    if not area:
        area = find_area(context, "IMAGE_EDITOR")
        if not area:
            return

    ctx = get_context_for_area(area)
    bpy.ops.image.view_all(ctx, fit_view=True)


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
