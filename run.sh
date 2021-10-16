#!/bin/bash
while read line
do
  if test "$line" != "" ; then
    heroku config:set $line
  fi
done < ./.env
heroku config:set GOOGLE_APPLICATION_CREDENTIALS=google-credentials.json
heroku config:set GOOGLE_CREDENTIALS="$(< ./google-credentials.json)"