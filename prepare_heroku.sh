#!/usr/bin/env sh

# init environment variables
heroku config:set PLATFORM=HEROKU
heroku config:set FLASK_APP=myfestival.py
