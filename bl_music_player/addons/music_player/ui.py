from typing import Any
import bpy


def MV_TOPBAR_upper_bar(self: Any, context: bpy.types.Context) -> None:
    layout: bpy.types.UILayout = self.layout
    row = layout.row(align=True)
    row.operator("wm.quit_blender", text="Quit", icon="QUIT")


def MV_TOPBAR_MT_file_menu_draw(self: Any, context: bpy.types.Context) -> None:
    self.layout.menu("MV_TOPBAR_MT_file_menu")


def MV_TOPBAR_MT_window_menu_draw(self: Any, context: bpy.types.Context) -> None:
    self.layout.menu("MV_TOPBAR_MT_window_menu")


class MV_TOPBAR_MT_file_menu(bpy.types.Menu):
    bl_idname = "MV_TOPBAR_MT_file_menu"
    bl_label = "File"

    def draw(self, context: bpy.types.Context) -> None:
        MV_TOPBAR_upper_bar(self, context)


class MV_TOPBAR_MT_window_menu(bpy.types.Menu):
    bl_idname = "MV_TOPBAR_MT_window_menu"
    bl_label = "Window"

    def draw(self, context: bpy.types.Context) -> None:
        layout: bpy.types.UILayout = self.layout
        row = layout.row(align=True)
        row.operator("wm.window_fullscreen_toggle", icon="FULLSCREEN_ENTER")


# ----------------REGISTER--------------.

classes = [MV_TOPBAR_MT_file_menu, MV_TOPBAR_MT_window_menu]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_editor_menus.append(MV_TOPBAR_MT_file_menu_draw)
    bpy.types.TOPBAR_MT_editor_menus.append(MV_TOPBAR_MT_window_menu_draw)


def unregister():
    # Remove header draw handler.
    bpy.types.TOPBAR_MT_editor_menus.remove(MV_TOPBAR_MT_file_menu_draw)
    bpy.types.TOPBAR_MT_editor_menus.remove(MV_TOPBAR_MT_window_menu_draw)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
