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

from music_player import (
    config,
    opsdata,
    ops,
    shortcuts,
    ui
)

logger = config.LoggerFactory.getLogger(__name__)

bl_info = {
    'name': 'BL Music Player',
    'author': 'B Rad C',
    'description': 'Blender music player addon',
    'blender': (4, 3, 0),
    'version': (0, 2, 0),
}

_need_reload = 'ops' in locals()

if _need_reload:
    import importlib

    config = importlib.reload(config)
    opsdata = importlib.reload(opsdata)
    ops = importlib.reload(ops)
    shortcuts = importlib.reload(shortcuts)
    ui = importlib.reload(ui)


def register():
    print('Addon Register', __file__)
    ops.register()
    shortcuts.register()
    ui.register()


def unregister():
    print('Addon Unregister', __file__)
    ui.unregister()
    shortcuts.unregister()
    ops.unregister()


if __name__ == '__main__':
    register()
