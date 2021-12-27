#!/usr/bin/env sh

# add postgres
heroku addons:add heroku-postgresql:hobby-dev

# init environment variables
heroku config:set PLATFORM=HEROKU
heroku config:set FLASK_APP=myfestival.py
