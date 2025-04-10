# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8-80 compliant>
import os
import bpy
from bl_app_override.helpers import AppOverrideState


def draw_left_override(self, context: bpy.types.Context):
    layout: bpy.types.UILayout = self.layout
    bpy.types.TOPBAR_MT_editor_menus.draw_collapsible(context, layout)


class AppStateStore(AppOverrideState):
    # Just provides data & callbacks for AppOverrideState
    __slots__ = ()

    @staticmethod
    def class_ignore():
        classes = []

        bpy.types.STATUSBAR_HT_header.draw = lambda self, context: None
        bpy.types.FILEBROWSER_HT_header.draw = lambda self, context: None
        bpy.types.GRAPH_HT_header.draw = lambda self, context: None
        bpy.types.SEQUENCER_HT_header.draw = lambda self, context: None
        bpy.types.VIEW3D_HT_header.draw = lambda self, context: None
        bpy.types.TOPBAR_HT_upper_bar.draw_left = draw_left_override
        bpy.types.TOPBAR_HT_upper_bar.draw_right = lambda self, context: None
        bpy.types.TOPBAR_MT_editor_menus.draw = lambda self, context: None
        
        return classes

    # ----------------
    # UI Filter/Ignore

    @staticmethod
    def ui_ignore_classes():
        # What does this do?
        return ()

    @staticmethod
    def ui_ignore_operator(op_id):
        return True

    @staticmethod
    def ui_ignore_property(ty, prop):
        return True

    @staticmethod
    def ui_ignore_menu(menu_id):
        return True

    @staticmethod
    def ui_ignore_label(text):
        return True

    # -------
    # Add-ons

    @staticmethod
    def addon_paths():
        addons = os.path.normpath(os.path.join(os.path.dirname(__file__), 'addons'))
        return (addons,)

    @staticmethod
    def addons():
        return ('music_player',)


app_state = AppStateStore()
active_load_post_handlers = []


def register():

    print('Template Register', __file__)
    app_state.setup()


def unregister():
    print('Template Unregister', __file__)
    app_state.teardown()

    for handler in reversed(active_load_post_handlers):
        bpy.app.handlers.load_post.remove(handler)
