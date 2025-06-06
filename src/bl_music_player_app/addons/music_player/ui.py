from typing import Any
import bpy


#
# menus
#

def MP_TOPBAR_draw(self, _) -> None:
    self.layout.menu('MP_TOPBAR_MT_file_menu')
    self.layout.menu('MP_TOPBAR_MT_player_menu')
    self.layout.menu('MP_TOPBAR_MT_window_menu')

class MP_TOPBAR_MT_file_menu(bpy.types.Menu):
    bl_idname = 'MP_TOPBAR_MT_file_menu'
    bl_label = 'File'

    def draw(self, _) -> None:
        row = self.layout.row(align=True)
        row.operator('wm.quit_blender', text='Quit', icon='QUIT')


class MP_TOPBAR_MT_player_menu(bpy.types.Menu):
    bl_idname = 'MP_TOPBAR_MT_player_menu'
    bl_label = 'Player'

    def draw(self, _) -> None:
        row = self.layout.column(align=True)

        row.operator('music_player.stop', text='Stop', icon='SNAP_FACE')
        row.separator()

        row.operator('music_player.randomize_visualizer', text='Randomize visualizer', icon='BLANK1')
        row.separator()

        row.label(text='Select visualizer', icon='BLANK1')

        wave_icon = 'PINNED' if bpy.context.scene.name == 'arctic wave' else 'BLANK1'
        row.operator('music_player.set_arctive_wave', text='arctive wave', icon=wave_icon)

        broken_icon = 'PINNED' if bpy.context.scene.name == 'broken radio' else 'BLANK1'
        row.operator('music_player.set_broken_radio', text='broken radio', icon=broken_icon)

        combo_icon = 'PINNED' if bpy.context.scene.name == 'combo wave' else 'BLANK1'
        row.operator('music_player.set_combo_wave', text='combo wave', icon= combo_icon)
        

class MP_TOPBAR_MT_window_menu(bpy.types.Menu):
    bl_idname = 'MP_TOPBAR_MT_window_menu'
    bl_label = 'Window'

    def draw(self, _) -> None:
        layout: bpy.types.UILayout = self.layout
        column = layout.column(align=True)
        column.operator('music_player.fullscreen', icon='FULLSCREEN_ENTER')
        column.operator('wm.window_fullscreen_toggle', icon='FULLSCREEN_ENTER')

#
# register
#

classes = [MP_TOPBAR_MT_file_menu, MP_TOPBAR_MT_player_menu, MP_TOPBAR_MT_window_menu]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_editor_menus.append(MP_TOPBAR_draw)


def unregister():
    bpy.types.TOPBAR_MT_editor_menus.remove(MP_TOPBAR_draw)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
