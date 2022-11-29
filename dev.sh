#!/bin/bash

#
# init
#

set -e

APP_NAME='bl_music_player'
BL_BIN='/Applications/Blender.app/Contents/MacOS/Blender'
BL_APP_TEMPLATE_FOLDER='/Users/brad/Library/Application Support/Blender/3.3/scripts/startup/bl_app_templates_user'

BL_APP_TEMPLATE_LINK="${BL_APP_TEMPLATE_FOLDER}/${APP_NAME}"
CURRENT_DIRECTORY=`pwd`
APP_SOURCE="${CURRENT_DIRECTORY}/${APP_NAME}"
SITE_PACKAGES="${CURRENT_DIRECTORY}/venv/lib/python3.10/site-packages"
ADDON_PATH="${APP_SOURCE}/addons"

HELP='this is a help menu.'

#
# run command
#

MODE="$1"

if [ "$MODE" = "start" ] || [ "$MODE" = "" ]; then
    clear; 
    PYTHONPATH="${SITE_PACKAGES}:${ADDON_PATH}" "$BL_BIN" --app-template "${APP_NAME}";

elif [ "$MODE" = 'link' ]; then
    ln -s "$APP_SOURCE" "$BL_APP_TEMPLATE_FOLDER"
    echo -e "linked:\n\t${APP_SOURCE}\n   ->\n\t${BL_APP_TEMPLATE_FOLDER}"

elif [ "$MODE" = 'unlink' ]; then
    unlink "${BL_APP_TEMPLATE_LINK}"
    echo "unlinked: ${BL_APP_TEMPLATE_LINK}"
    
elif [ "$MODE" = 'help' ]; then
    echo -e "${HELP}"
    echo "${SITE_PACKAGES}"
    echo "${ADDON_PATH}"

else
    echo -e "error, unknown command: ${MODE}\n${HELP}"
fi