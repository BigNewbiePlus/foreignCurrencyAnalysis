#!/bin/sh
export DISPLAY=:1    
Xvfb $DISPLAY -ac -screen 0 1280x1024x8 &

/etc/init.d/cron start
tail -F /var/log/cron.log
