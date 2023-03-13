#!/bin/bash

sudo cp govscent.service /etc/systemd/system/
sudo systemctl enable govscent
sudo systemctl restart govscent
