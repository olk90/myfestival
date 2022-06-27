#!/usr/bin/env sh

# create app, pass name as parameter!
heroku apps:create $1 --region eu

# add postgres
heroku addons:add heroku-postgresql:hobby-dev

# init environment variables
heroku config:set PLATFORM=HEROKU
heroku config:set FLASK_APP=myfestival.py
heroku config:set INITIAL_ADMIN_PW=vspw4mf
