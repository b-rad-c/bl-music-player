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


ASSET_DIRECTORY = Path(__file__).parent / 'assets'


class LoggerFactory:

    """
    Utility class to streamline logger creation
    """

    @staticmethod
    def getLogger(name=__name__):
        logger = logging.getLogger(name)
        return logger


def get_config_file() -> Path:
    path = bpy.utils.user_resource("CONFIG", path="music_player", create=True)
    return Path(path) / "config.json"


def save_config(config: dict):
    with open(get_config_file().as_posix(), 'w') as f:
        json.dump(config, f, indent=4)


def load_config():
    path = get_config_file()

    # make config file if it doesn't exist
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        default_config = {}
        save_config(default_config)
        print(f"Created config file: {path.as_posix()}")
        return default_config
    else:
        with open(path.as_posix(), "r") as file:
            return json.load(file)
