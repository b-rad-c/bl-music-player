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
import bpy
from music_player.ops import MV_OT_fullscreen


addon_keymaps = []

def register_keymaps():
    global addon_keymaps

    # Turn off autosave prefs.
    bpy.context.preferences.use_preferences_save = False

    # view_3d_area = opsdata.find_area(bpy.context, 'VIEW_3D')
    # view_3d_context = opsdata.get_context_for_area(view_3d_area)

    # with bpy.context.temp_override(**view_3d_context):
    keymap = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name='Screen', space_type='EMPTY', region_type='WINDOW')


    # addon_keymaps.append(
    #     (
    #         keymap,
    #         keymap.keymap_items.new(
    #             'wm.window_fullscreen_toggle', value='PRESS', type='F', head=True
    #         ),
    #     )
    # )
   
    addon_keymaps.append(
        (
            keymap,
            keymap.keymap_items.new(
                MV_OT_fullscreen.bl_idname, value='PRESS', type='F', head=True
            ),
        )
    )

    bpy.context.window_manager.keyconfigs.update()

def register():
    if not bpy.app.background:
        register_keymaps()


def unregister_keymaps():
    global addon_keymaps
    if not bpy.app.background:
        for km, kmi in addon_keymaps:
            try:
                km.keymap_items.remove(kmi)
            except ReferenceError:
                # Happens when you press CTRL+Q, I guess this means that this keymap item is already removed?
                pass
        addon_keymaps.clear()


def unregister():
    # Unregister Hotkeys.
    # Does not work if blender runs in background.
    if not bpy.app.background:
        unregister_keymaps()

    # Handlers
    # bpy.app.handlers.load_post.remove(delete_shortcuts_load_post)
