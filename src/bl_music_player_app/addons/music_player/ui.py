import bpy
from .ops import visualizers


#
# menus
#

class MP_TOPBAR_MT_file_menu(bpy.types.Menu):
    bl_idname = 'MP_TOPBAR_MT_file_menu'
    bl_label = 'File'

    def draw(self, _) -> None:
        row = self.layout.row(align=True)
        row.operator('wm.quit_blender', text='Quit', icon='QUIT')

class MP_TOPBAR_MT_browser_menu(bpy.types.Menu):
    bl_idname = 'MP_TOPBAR_MT_browser_menu'
    bl_label = 'Browser'

    def draw(self, _) -> None:
        layout: bpy.types.UILayout = self.layout
        column = layout.column(align=True)
        column.operator('music_player.text_scroll_up', icon='SORT_DESC')
        column.operator('music_player.text_scroll_down', icon='SORT_ASC')


class MP_TOPBAR_MT_player_menu(bpy.types.Menu):
    bl_idname = 'MP_TOPBAR_MT_player_menu'
    bl_label = 'Player'

    def draw(self, context) -> None:
        row = self.layout.column(align=True)
        row.operator('music_player.stop', text='Stop', icon='SNAP_FACE')


class MP_TOPBAR_MT_visualizer_menu(bpy.types.Menu):
    bl_idname = 'MP_TOPBAR_MT_visualizer_menu'
    bl_label = 'Visualizer'

    def draw(self, context) -> None:
        row = self.layout.column(align=True)

        row.operator('music_player.sync_to_microphone', text='Sync to microphone', icon='REC')
        row.operator('music_player.sync_debug', text='Sync Debug', icon='BLANK1')
        row.separator()

        row.operator('music_player.randomize_visualizer', text='Randomize visualizer', icon='BLANK1')
        row.separator()

        row.label(text='Select visualizer', icon='BLANK1')

        for visualizer in visualizers:
            if context.scene.active_visualizer == visualizer['id']:
                wave_icon = 'CHECKMARK'
            else:
                wave_icon = 'BLANK1'

            row.operator(
                'music_player.set_' + visualizer['id'], 
                text=visualizer['label'],
                icon=wave_icon
            )
        

class MP_TOPBAR_MT_window_menu(bpy.types.Menu):
    bl_idname = 'MP_TOPBAR_MT_window_menu'
    bl_label = 'Window'

    def draw(self, _) -> None:
        layout: bpy.types.UILayout = self.layout
        column = layout.column(align=True)
        column.operator('music_player.fullscreen', icon='FULLSCREEN_ENTER')
        column.operator('wm.window_fullscreen_toggle', icon='FULLSCREEN_ENTER')

def MP_TOPBAR_draw(self, _) -> None:
    self.layout.menu('MP_TOPBAR_MT_file_menu')
    self.layout.menu('MP_TOPBAR_MT_browser_menu')
    self.layout.menu('MP_TOPBAR_MT_player_menu')
    self.layout.menu('MP_TOPBAR_MT_visualizer_menu')
    self.layout.menu('MP_TOPBAR_MT_window_menu')

#
# UI Panels
#

class MP_PT_visualizer_settings(bpy.types.Panel):
    """Panel for visualizer settings in the Properties window"""
    bl_label = 'Music Player Visualizer'
    bl_idname = 'MP_PT_visualizer_settings'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'scene'

    def draw(self, context):
        layout = self.layout
        layout.label(text='Hello World - Visualizer Settings')
        layout.label(text='Configuration panel coming soon!')

#
# register
#

classes = [
    MP_TOPBAR_MT_file_menu, 
    MP_TOPBAR_MT_browser_menu,
    MP_TOPBAR_MT_player_menu, 
    MP_TOPBAR_MT_visualizer_menu,
    MP_TOPBAR_MT_window_menu,
    MP_PT_visualizer_settings
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_editor_menus.append(MP_TOPBAR_draw)


def unregister():
    bpy.types.TOPBAR_MT_editor_menus.remove(MP_TOPBAR_draw)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
