# Blender App Template Sample - Music Player

An example Blender App Template music player with sound activated blender music visualizer.

Tested on Blender 3.6 with Python 3.10, this is very much a proof of concept app, it has bugs and limited functionality, but is an awesome demonstration of Blender App Templates!


# usage
To setup a local dev environment from source:

```bash
git clone https://github.com/b-rad-c/bl-music-player.git
cd bl-music-player
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
python -m blenv setup
```

After setup, to run the gui app:

```bash
python -m blenv blender
```


# Credit

Songs included in this application are available under a creative commons license, no changes were made to any songs. Links for each song including artist and license are available in `./src/music_player/music/credit` and are also distributed in the packaged .zip version of the app.