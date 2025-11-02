#!/bin/bash

cd "$(dirname "$0")" || exit

source venv/bin/activate

python3 main.py -d > logfile.log 2>&1 &

deactivate