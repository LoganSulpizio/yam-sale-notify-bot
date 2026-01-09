#!/bin/bash
set -e

# ----------------------------------------
# Yam Sale Notify bot Docker Entrypoint
# ----------------------------------------
# Responsibilities:
# 1. Verify that YAM_SALE_NOTIFY_BOT_TOKEN is set.
# 2. Start the bot.
# ----------------------------------------

echo "Starting YAM Sale Notify Bot bot container..."

# Move into the application directory (must match WORKDIR in Dockerfile)
cd /app

# 1) Ensure BOT_REALTOKENS_UPDATE_ALERTS_TOKEN is provided
if [ -z "$YAM_SALE_NOTIFY_BOT_TOKEN" ]; then
  echo "ERROR: environment variable YAM_SALE_NOTIFY_BOT_TOKEN is not set."
  echo "Please define it in your .env file or your GitHub Secrets"
  exit 1
fi


# 2) Start the bot
echo "Launching YAM Sale Notify Bot..."
exec python3 -m bot.main