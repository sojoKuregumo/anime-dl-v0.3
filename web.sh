#!/bin/bash

# Start aria2 in the background for downloading
aria2c --enable-rpc --rpc-listen-all=false --rpc-listen-port=6800 --daemon=true --dir=downloads

# Process environment variables if provided
if [ -n "$VARS" ]; then
  # Install jq temporarily for parsing (if not already installed)
  if ! command -v jq &> /dev/null; then
    apt-get update && apt-get install -y jq
  fi
  
  # Parse JSON environment variables
  eval $(echo "$VARS" | jq -r 'to_entries | .[] | "export \(.key)=\"\(.value)\""')
fi

# Start the Python bot in the background
python3 bot.py &

# Run the Flask web server to keep the service alive (required by Koyeb)
gunicorn app:app -b 0.0.0.0:8080
