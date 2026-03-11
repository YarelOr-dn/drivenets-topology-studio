#!/bin/bash

# Deployment Script for Topology Editor
# Usage: ./deploy.sh

# Configuration
SERVER="dn@h263"
REMOTE_PATH="/var/www/html"  # ⚠️ CHANGE THIS to your actual web directory path
LOCAL_PATH="/Users/yarelor/Library/CloudStorage/OneDrive-DrivenetsLTD/CURSOR"

echo "🚀 Deploying Topology Editor to h263..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Navigate to project directory
cd "$LOCAL_PATH" || exit 1

# Show what will be uploaded
echo "📦 Files to upload:"
echo "   ✓ index.html"
echo "   ✓ topology.js"
echo "   ✓ topology-momentum.js"
echo "   ✓ topology-history.js"
echo "   ✓ debugger.js"
echo "   ✓ styles.css"
echo ""

# Create backup on server first
echo "💾 Creating backup on server..."
ssh $SERVER "cd $REMOTE_PATH && \
    mkdir -p backups && \
    cp index.html backups/index.html.backup_\$(date +%Y%m%d_%H%M%S) 2>/dev/null || true && \
    cp topology.js backups/topology.js.backup_\$(date +%Y%m%d_%H%M%S) 2>/dev/null || true"

echo "✅ Backup created"
echo ""

# Upload all project files using rsync
echo "📤 Uploading files..."
rsync -avz --progress \
    --include='*.html' \
    --include='*.js' \
    --include='*.css' \
    --exclude='*.md' \
    --exclude='*.backup*' \
    --exclude='*.snapshot*' \
    --exclude='.git/' \
    --exclude='backups/' \
    index.html \
    topology.js \
    topology-momentum.js \
    topology-history.js \
    debugger.js \
    styles.css \
    $SERVER:$REMOTE_PATH/

# Check if upload was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Deployment successful!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📊 Deployment Summary:"
    echo "   Server: h263"
    echo "   Path: $REMOTE_PATH"
    echo "   Date: $(date)"
    echo ""
    echo "🧪 Next steps:"
    echo "   1. Open your application in browser"
    echo "   2. Hard refresh (Cmd+Shift+R)"
    echo "   3. Test new VLAN manipulation features"
    echo "   4. Test text rotation features"
    echo ""
    echo "🔐 IMPORTANT: Change your server password!"
    echo ""
else
    echo ""
    echo "❌ Deployment failed!"
    echo "   Check your connection and try again"
    exit 1
fi

