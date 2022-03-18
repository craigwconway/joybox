#!/bin/bash

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate

cp ./joybox.service ~/.config/systemd/user/joybox.service
chown pi:pi ~/.config/systemd/user/joybox.service 
systemctl --user enable joybox.service
systemctl --user start joybox
systemctl --user status joybox
