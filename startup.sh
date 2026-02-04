#!/bin/bash

openssl rand -hex 32 > /app/git_hash

if [ $ENABLE_CRON == "True" ];
then
echo "Starting Python Cron"
python /bin/scheduler.py /app/python-cron /app/logs/python-cron.log &
status=$?
if [ $status -ne 0 ]; then
  echo "Failed to start cron: $status"
  exit $status
fi

fi

if [ $ENABLE_WEB == "True" ];
    then
echo "Starting Gunicorn"
# Start the second process

current_host=$(hostname)
echo "accesslog = '/app/logs/gunicorn-access-$current_host.log'" >> /app/gunicorn.ini
echo "errorlog = '/app/logs/gunicorn-error-$current_host.log'"  >> /app/gunicorn.ini

/app/venv/bin/gunicorn queuemanager.wsgi --bind :8080 --config /app/gunicorn.ini
status=$?
if [ $status -ne 0 ]; then
  echo "Failed to start gunicorn: $status"
  exit $status
fi
else
   echo "ENABLE_WEB environment vairable not set to True, web server is not starting."
   /bin/bash
fi
