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
from music_player.ops import MP_TEXT_SCROLL_UP, MP_TEXT_SCROLL_DOWN, MP_ON_CLICK
from music_player.ops import MP_OT_fullscreen


addon_keymaps = []
keymap = None

def remove_default_keymaps():
    keys = bpy.context.window_manager.keyconfigs

    for key, value in keys.items():
        for km in value.keymaps:
            for kmi in km.keymap_items:
                if kmi.type in ['WHEELINMOUSE', 'WHEELOUTMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE']:
                    # print(f'    removed {km.name} - {kmi.idname} - {kmi.type} {kmi.value} ({kmi.active})')
                    km.keymap_items.remove(kmi)
                elif '3d' in km.name.lower() and kmi.type in ['LEFTMOUSE', 'RIGHTMOUSE', 'MIDDLEMOUSE', 'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE']:
                    # print(f'    >> {km.name} - {kmi.idname} - {kmi.type} {kmi.value} ({kmi.active})')
                    km.keymap_items.remove(kmi)

def register_keymaps():
    global addon_keymaps
    global keymap

    bpy.context.preferences.use_preferences_save = False
    keymap = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name='Screen', space_type='EMPTY', region_type='WINDOW')

    addon_keymaps.extend(
        [
            keymap.keymap_items.new(
                MP_OT_fullscreen.bl_idname, value='PRESS', type='F', head=True
            ),
            keymap.keymap_items.new(
                MP_TEXT_SCROLL_UP.bl_idname, value='PRESS', type='UP_ARROW', head=True
            ),
            keymap.keymap_items.new(
                MP_TEXT_SCROLL_UP.bl_idname, value='ANY', type='WHEELDOWNMOUSE', head=True
            ),
            keymap.keymap_items.new(
                MP_TEXT_SCROLL_DOWN.bl_idname, value='PRESS', type='DOWN_ARROW', head=True
            ),
            keymap.keymap_items.new(
                MP_TEXT_SCROLL_DOWN.bl_idname, value='ANY', type='WHEELUPMOUSE', head=True
            ),
            keymap.keymap_items.new(
                MP_ON_CLICK.bl_idname, value='PRESS', type='LEFTMOUSE', head=True
            ),
            keymap.keymap_items.new(
                MP_ON_CLICK.bl_idname, value='PRESS', type='RIGHTMOUSE', head=True
            ),
            keymap.keymap_items.new(
                MP_ON_CLICK.bl_idname, value='PRESS', type='MIDDLEMOUSE', head=True
            ),
            keymap.keymap_items.new(
                MP_ON_CLICK.bl_idname, value='PRESS', type='INBETWEEN_MOUSEMOVE', head=True
            ),
            keymap.keymap_items.new(
                MP_ON_CLICK.bl_idname, value='PRESS', type='MOUSEMOVE', head=True
            )
        ]
    )

    bpy.context.window_manager.keyconfigs.update()

def register():
    if not bpy.app.background:
        remove_default_keymaps()
        register_keymaps()


def unregister_keymaps():
    global addon_keymaps
    global keymap
    if not bpy.app.background:
        for kmi in addon_keymaps:
            try:
                keymap.keymap_items.remove(kmi)
            except ReferenceError:
                # Happens when you press CTRL+Q, I guess this means that this keymap item is already removed?
                pass
        addon_keymaps.clear()


def unregister():
    # Unregister Hotkeys.
    # Does not work if blender runs in background.
    if not bpy.app.background:
        unregister_keymaps()
