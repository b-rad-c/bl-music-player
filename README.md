# Blender App Template Sample - Music Player

An example Blender App Template music player with sound activated blender music visualizer.

Tested on Blender 3.6 with Python 3.10, this is very much a proof of concept app, it has bugs and limited functionality, but is an awesome demonstration of Blender App Templates!

# Use template 
You can use the app without downloading this repo and setting up a development environment.

Download zip file in `./dist` folder and install and run like a normal blender app template.

Run the application and single click on a song in the list, press the F key to toggle full screen.

# Dev usage
To setup a local dev environment and run from source:

```bash
git clone https://github.com/b-rad-c/bl-music-player.git
cd bl-music-player
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

An included shell script helps with setting up and running the code.

*Note that you may need to update variables in this script because this example app is setup for OSX with Blender3.6 and a python3.10 local venv*

```bash
# this links the code to your blender install's app template folder
./dev.sh link

# run the app template
./dev.sh start
```

You will need to quit and re-run the start command to load code changes.

To unlink the code from your blender install:
```bash
./dev.sh unlink
```

To package into a zip for distributing:
```bash
./dev.sh package
```

# Credit

Songs included in this application are available under a creative commons license, no changes were made to any songs. Links for each song including artist and license are available in `./src/music_player/music/credit` and are also distributed in the packaged .zip version of the app.