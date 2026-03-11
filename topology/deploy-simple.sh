#!/bin/bash

# Simple One-Line Deployment Script
# Just uploads the essential files

SERVER="dn@h263"
REMOTE_PATH="/var/www/html"  # ⚠️ CHANGE THIS if different

echo "🚀 Uploading files to h263..."

cd "/Users/yarelor/Library/CloudStorage/OneDrive-DrivenetsLTD/CURSOR"

scp index.html topology.js topology-momentum.js topology-history.js debugger.js styles.css $SERVER:$REMOTE_PATH/

echo "✅ Done! Refresh your browser (Cmd+Shift+R)"

