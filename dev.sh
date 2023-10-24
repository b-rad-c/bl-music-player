#!/bin/bash

#
# init
#

APP_NAME='bl_music_player'
APP_VERSION='0.0.0'

BL_BIN='/Applications/Blender.app/Contents/MacOS/Blender'
BL_APP_TEMPLATE_FOLDER='/Users/brad/Library/Application Support/Blender/3.6/scripts/startup/bl_app_templates_user'
BL_APP_TEMPLATE_LINK="${BL_APP_TEMPLATE_FOLDER}/${APP_NAME}"

CURRENT_DIRECTORY=`pwd`
APP_SOURCE="${CURRENT_DIRECTORY}/${APP_NAME}"
SITE_PACKAGES="${CURRENT_DIRECTORY}/venv/lib/python3.10/site-packages"
ADDON_PATH="${APP_SOURCE}/addons"
DIST_PATH="dist/${APP_NAME}-${APP_VERSION}.zip"

HELP='i am a help menu. i am not much help. sorry. think of me more as a reminder that good times lie ahead than a piece of documentation.'

#
# run command
#

MODE="$1"

if [ "$MODE" = "start" ] || [ "$MODE" = "" ]; then
    clear; 
    PYTHONPATH="${SITE_PACKAGES}:${ADDON_PATH}" "$BL_BIN" --app-template "${APP_NAME}";

elif [ "$MODE" = 'link' ]; then
    ln -s "$APP_SOURCE" "$BL_APP_TEMPLATE_FOLDER"
    if [ $? -eq 0 ]; then 
        echo -e "linked:\n\t${APP_SOURCE}\n   ->\n\t${BL_APP_TEMPLATE_FOLDER}"
    else 
        echo "error linking app, you may need to create intermediate directories"
    fi

elif [ "$MODE" = 'unlink' ]; then
    unlink "${BL_APP_TEMPLATE_LINK}"
    echo "unlinked: ${BL_APP_TEMPLATE_LINK}"

elif [ "$MODE" = 'package' ]; then
    # remove __pycache__ folders and .DS_Store files
    find $APP_NAME -name __pycache__ -type d -print0 | xargs -0 rm -r --
    find $APP_NAME -name .DS_Store -type f -print0 | xargs -0 rm  --
    find $APP_NAME -name "*blend1" -type f -print0 | xargs -0 rm  --

    # Create dist folder.
    if ! [[ -d "dist" ]]
    then
        mkdir -p "dist"
    fi

    # zip it all up.
    zip -r $DIST_PATH $APP_NAME
    echo "\nzipped $APP_NAME to $DIST_PATH"
   
elif [ "$MODE" = 'help' ]; then
    echo -e "${HELP}"
    echo "${SITE_PACKAGES}"
    echo "${ADDON_PATH}"

else
    echo -e "error, unknown command: ${MODE}\n${HELP}"
fi