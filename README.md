# Blender App Template Sample - Music Player

A music visualizer made with blender. It has a gui music player (blender app template) that allows you to select and play music files from your computer. It will bake the audio samples to drive a geo nodes animation synced to the music.

It also has a cli (blender as a python module) to render a video file of the animation with a given audio file.

Current version is tested with blender 4.4 and python 3.11.

This is a proof of concept app, it has limited functionality and may not fully work as expected. But it is a demo of blender app templates and well as blender as a python module. It shows how you can reuse code between two blender apps.

# usage
* download zip file from `dist` directory
* click the blender logo in the topbar then "Install Application Template"
* select zip file
* File > New > Bl Music Player App

# development
To setup a local dev environment from source:

```bash
git clone https://github.com/b-rad-c/bl-music-player.git
cd bl-music-player
python3 -m venv .venv   # use python version compatible with your blender's python
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
python -m blenv setup
```

`blenv` is a blender env manager similar to `venv` for blender projects. It's another of my projects, see https://github.com/medium-tech/bl-env for more info.

To run the app template (gui):

```bash
python -m blenv blender
```

Render visualizer video for an audio file:

```bash
./src/cli.py --audio sample.wav --output out/sample.mp4
```

# Credit

Songs included in this application are available under a creative commons license, no changes were made to any songs. Links for each song including artist and license are available in `./src/music_player/music/credit` and are also distributed in the packaged .zip version of the app.

I made the visualizer following this tutorial: https://www.youtube.com/watch?v=rSrjDgWWlWs