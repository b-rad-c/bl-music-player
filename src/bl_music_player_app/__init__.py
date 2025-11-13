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

import os

import bl_ui
import bpy
from bl_app_override.helpers import AppOverrideState


def draw_topbar_upper_bar_left(self, context: bpy.types.Context):
    layout: bpy.types.UILayout = self.layout
    bpy.types.TOPBAR_MT_editor_menus.draw_collapsible(context, layout)

def draw_properties_header(self, context: bpy.types.Context):
    self.layout.label(text='Music Player Configuration', icon='MUSIC')

empty = lambda self, context: None

class AppStateStore(AppOverrideState):
    # Just provides data & callbacks for AppOverrideState
    __slots__ = ()

    @staticmethod
    def class_ignore():
        classes = []

        bpy.types.STATUSBAR_HT_header.draw = empty
        bpy.types.FILEBROWSER_HT_header.draw = empty
        bpy.types.GRAPH_HT_header.draw = empty
        bpy.types.SEQUENCER_HT_header.draw = empty
        bpy.types.VIEW3D_HT_header.draw = empty
        bpy.types.TOPBAR_HT_upper_bar.draw_left = draw_topbar_upper_bar_left
        bpy.types.TOPBAR_HT_upper_bar.draw_right = empty
        bpy.types.TOPBAR_MT_editor_menus.draw = empty
        bpy.types.SEQUENCER_PT_tools_active.draw = empty
        bpy.types.SEQUENCER_PT_tools_active.draw_cls = lambda cls, layout, context, detect_layout=True, scale_y=1.75: None
        bpy.types.VIEW3D_PT_overlay.draw = empty
        bpy.types.VIEW3D_PT_overlay_guides.draw = empty
        bpy.types.VIEW3D_PT_view3d_lock.draw = empty
        bpy.types.VIEW3D_MT_view_cameras.draw = empty


        #bpy.types.PROPERTIES_PT_navigation_bar.draw = empty
        #bpy.types.PROPERTIES_PT_options.draw = empty

        #bpy.types.PROPERTIES_HT_header.draw = draw_properties_header

        # bl_ui.space_properties.PROPERTIES_HT_header.draw = empty
        #bpy.types.SpaceProperties.show_region_header = False       

        classes = []

        def func(cls):
            ignore = False
            # if cls.__name__.startswith('PROPERTIES'):
            #     ignore = True
            #     print('Ignoring PROPERTIES class:', cls.__name__)
            # if cls.__name__.startswith('OBJECT'):
            #     ignore = True
            #     print('Ignoring OBJECT class:', cls.__name__)
            # Ignore Scene context panels except our custom one
            if hasattr(cls, 'bl_context') and cls.bl_context == 'scene' and cls.__name__ != 'MP_PT_visualizer_settings':
                ignore = True
                print('Ignoring Scene panel:', cls.__name__)

            return ignore

        for cls in filter(func, bpy.types.Panel.__subclasses__()):
            classes.append(cls)

        # for attr in dir(bpy.types):
        #     if ('VIEW3D' in attr or 'view3d' in attr) and not 'tools' in attr:
        #         print(attr)

        # ta = bpy.types.SEQUENCER_PT_tools_active
        # for name in dir(ta):
        #     print(name, getattr(ta, name))
        # breakpoint()

        print('done ignoring classes')

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
