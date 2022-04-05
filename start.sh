#!/bin/bash

cd /home/pi/joybox
source venv/bin/activate
export FLASK_APP=joybox/app.py;flask run --host=0.0.0.0
