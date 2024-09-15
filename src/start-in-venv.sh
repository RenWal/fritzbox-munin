#!/bin/bash

VENV=$(ls -d ~munin/venv)

MY_ORG_SCRIPT="$0"
MY_SCRIPT_PATH=$(readlink -e "$MY_ORG_SCRIPT")
MY_SCRIPT_NAME=$(basename "$MY_ORG_SCRIPT")

MY_BASE_PATH=$(dirname "$MY_SCRIPT_PATH" )
if [ "${MY_BASE_PATH:0:1}" != "/" ] ; then
        MY_BASE_PATH="$PWD/$MY_BASE_PATH"
fi

PY_SCRIPT="$MY_BASE_PATH/"$(echo "$MY_SCRIPT_NAME" | sed 's:\.sh$:\.py:')

source $VENV/bin/activate

# in case the venv is on a filesystem without executable flags set:
$VENV/bin/python3 "$PY_SCRIPT"  "$@"

