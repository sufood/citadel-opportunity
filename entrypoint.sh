#!/bin/bash
set -e

# Start uvicorn in the background
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &
UVICORN_PID=$!

# Start nginx in the foreground (primary process)
nginx -g "daemon off;" &
NGINX_PID=$!

# If either process exits, shut down the other
trap "kill $UVICORN_PID $NGINX_PID 2>/dev/null; exit 0" SIGTERM SIGINT

# Wait for either process to exit — if one dies, stop the container
wait -n $UVICORN_PID $NGINX_PID
EXIT_CODE=$?

# Kill the remaining process
kill $UVICORN_PID $NGINX_PID 2>/dev/null
exit $EXIT_CODE
