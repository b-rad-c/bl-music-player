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
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # Microphone sampling settings
        box = layout.box()
        box.label(text="Microphone Settings", icon='REC')
        
        col = box.column(align=True)
        col.prop(scene, 'mp_gain_db', text='Gain (dB)')
        col.prop(scene, 'mp_sample_rate', text='Sample Rate')
        col.prop(scene, 'mp_output_rate', text='Output Rate (fps)')
        
        col.separator()
        col.prop(scene, 'mp_use_fft', text='Use FFT (4-band EQ)')
        col.prop(scene, 'mp_fft_size', text='FFT Size')
        
        # Processing settings
        box = layout.box()
        box.label(text="Processing", icon='MODIFIER')
        
        col = box.column(align=True)
        col.prop(scene, 'mp_smoothing', text='Smoothing', slider=True)
        col.prop(scene, 'mp_min_level', text='Min Level')
        
        col.separator()
        col.prop(scene, 'mp_compression_threshold', text='Compression Threshold', slider=True)
        col.prop(scene, 'mp_compression_ratio', text='Compression Ratio')
        
        # Debug settings
        box = layout.box()
        box.label(text="Debug", icon='CONSOLE')
        col = box.column(align=True)
        col.prop(scene, 'mp_quiet', text='Quiet Mode (hide ffmpeg output)')


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
    # Register Scene properties for MicSampleConfig
    bpy.types.Scene.mp_gain_db = bpy.props.FloatProperty(
        name="Gain (dB)",
        description="Gain in decibels. Typical range: 20-60 dB",
        default=25.0,
        min=0.0,
        max=100.0
    )
    
    bpy.types.Scene.mp_sample_rate = bpy.props.IntProperty(
        name="Sample Rate",
        description="Microphone sample rate (44100 recommended for FFT)",
        default=44100,
        min=8000,
        max=96000
    )
    
    bpy.types.Scene.mp_output_rate = bpy.props.IntProperty(
        name="Output Rate",
        description="How many times per second to yield samples (fps)",
        default=30,
        min=1,
        max=120
    )
    
    bpy.types.Scene.mp_fft_size = bpy.props.IntProperty(
        name="FFT Size",
        description="FFT window size (power of 2)",
        default=2048,
        min=256,
        max=8192
    )
    
    bpy.types.Scene.mp_min_level = bpy.props.FloatProperty(
        name="Min Level",
        description="Minimum threshold below which level is set to 0",
        default=0.0001,
        min=0.0,
        max=1.0,
        precision=4
    )
    
    bpy.types.Scene.mp_smoothing = bpy.props.FloatProperty(
        name="Smoothing",
        description="Exponential smoothing (0=none, 0.5=moderate, 0.9=heavy)",
        default=0.5,
        min=0.0,
        max=1.0,
        subtype='FACTOR'
    )
    
    bpy.types.Scene.mp_compression_threshold = bpy.props.FloatProperty(
        name="Compression Threshold",
        description="Level above which compression is applied",
        default=0.7,
        min=0.0,
        max=1.0,
        subtype='FACTOR'
    )
    
    bpy.types.Scene.mp_compression_ratio = bpy.props.FloatProperty(
        name="Compression Ratio",
        description="Ratio of compression above threshold (1.0=none, 4.0=4:1)",
        default=4.0,
        min=1.0,
        max=20.0
    )
    
    bpy.types.Scene.mp_use_fft = bpy.props.BoolProperty(
        name="Use FFT",
        description="Use FFT for 4-band EQ (if False, use simple RMS)",
        default=True
    )
    
    bpy.types.Scene.mp_quiet = bpy.props.BoolProperty(
        name="Quiet Mode",
        description="Suppress ffmpeg output",
        default=True
    )

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_editor_menus.append(MP_TOPBAR_draw)


def unregister():
    bpy.types.TOPBAR_MT_editor_menus.remove(MP_TOPBAR_draw)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    # Unregister Scene properties
    del bpy.types.Scene.mp_gain_db
    del bpy.types.Scene.mp_sample_rate
    del bpy.types.Scene.mp_output_rate
    del bpy.types.Scene.mp_fft_size
    del bpy.types.Scene.mp_min_level
    del bpy.types.Scene.mp_smoothing
    del bpy.types.Scene.mp_compression_threshold
    del bpy.types.Scene.mp_compression_ratio
    del bpy.types.Scene.mp_use_fft
    del bpy.types.Scene.mp_quiet
