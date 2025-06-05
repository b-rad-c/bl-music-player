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
import bpy
import json 
import logging

_parent_directory: Path     = Path(__file__).parent
MUSIC_DIRECTORY: Path       = _parent_directory / 'music'
VISUALIZER_DIRECTORY: Path  = _parent_directory / 'visualizers'
CONFIG_DIRECTORY: Path      = Path(bpy.utils.user_resource('CONFIG', path='music_player', create=True))
CONFIG_FILE_PATH: Path      = CONFIG_DIRECTORY / 'config.json'

DEFAULT_CONFIG = {}

class LoggerFactory:

    """
    Utility class to streamline logger creation
    """

    @staticmethod
    def getLogger(name=__name__):
        logger = logging.getLogger(name)
        return logger


def save_config(config: dict):
    with open(CONFIG_FILE_PATH.as_posix(), 'w+') as config_file:
        json.dump(config, config_file, indent=4)


def load_config():
    if not CONFIG_FILE_PATH.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    else:
        with open(CONFIG_FILE_PATH.as_posix(), 'r') as file:
            return json.load(file)
