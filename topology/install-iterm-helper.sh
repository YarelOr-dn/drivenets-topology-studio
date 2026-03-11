#!/bin/bash
# iTerm Split-Pane SSH Helper Installer
# This script installs a macOS service that enables automatic split-pane SSH connections
# from the Topology Creator web app.

set -e

echo "🚀 Installing iTerm Split-Pane SSH Helper..."
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create the helper script directory
HELPER_DIR="$HOME/.topology-creator"
mkdir -p "$HELPER_DIR"

# Create the AppleScript helper that handles split-pane SSH
cat > "$HELPER_DIR/iterm-split-ssh.scpt" << 'APPLESCRIPT'
on run argv
    set sshCommand to item 1 of argv
    
    tell application "iTerm"
        activate
        
        -- Check if iTerm has any windows
        if (count of windows) = 0 then
            -- No windows, create new one
            create window with default profile
            tell current session of current window
                write text sshCommand
            end tell
        else
            -- Window exists, split the current pane
            tell current session of current window
                set newSession to (split horizontally with default profile)
                tell newSession
                    write text sshCommand
                end tell
            end tell
        end if
    end tell
end run
APPLESCRIPT

echo -e "${GREEN}✓${NC} Created AppleScript helper"

# Create a shell wrapper
cat > "$HELPER_DIR/iterm-ssh" << 'SHELLSCRIPT'
#!/bin/bash
# iTerm Split-Pane SSH Wrapper
# Usage: iterm-ssh user@host

if [ -z "$1" ]; then
    echo "Usage: iterm-ssh user@host"
    exit 1
fi

SSH_CMD="ssh $1"
osascript "$HOME/.topology-creator/iterm-split-ssh.scpt" "$SSH_CMD"
SHELLSCRIPT

chmod +x "$HELPER_DIR/iterm-ssh"
echo -e "${GREEN}✓${NC} Created shell wrapper"

# Create a URL scheme handler app using osacompile
APP_DIR="$HOME/Applications"
mkdir -p "$APP_DIR"

# Create the app bundle structure
APP_PATH="$APP_DIR/iTerm-SSH-Handler.app"
rm -rf "$APP_PATH"
mkdir -p "$APP_PATH/Contents/MacOS"
mkdir -p "$APP_PATH/Contents/Resources"

# Create Info.plist with URL scheme handler
cat > "$APP_PATH/Contents/Info.plist" << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>handler</string>
    <key>CFBundleIdentifier</key>
    <string>com.topology-creator.iterm-ssh-handler</string>
    <key>CFBundleName</key>
    <string>iTerm SSH Handler</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleURLTypes</key>
    <array>
        <dict>
            <key>CFBundleURLName</key>
            <string>iTerm Split SSH</string>
            <key>CFBundleURLSchemes</key>
            <array>
                <string>iterm-ssh</string>
            </array>
        </dict>
    </array>
    <key>LSBackgroundOnly</key>
    <true/>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
</dict>
</plist>
PLIST

# Create the handler script
cat > "$APP_PATH/Contents/MacOS/handler" << 'HANDLER'
#!/bin/bash
# URL Handler for iterm-ssh:// scheme
# Receives URLs like: iterm-ssh://user@host

URL="$1"
# Extract user@host from URL (remove iterm-ssh:// prefix)
SSH_TARGET="${URL#iterm-ssh://}"

if [ -n "$SSH_TARGET" ]; then
    "$HOME/.topology-creator/iterm-ssh" "$SSH_TARGET"
fi
HANDLER

chmod +x "$APP_PATH/Contents/MacOS/handler"
echo -e "${GREEN}✓${NC} Created URL handler app"

# Register the URL scheme
echo -e "${BLUE}→${NC} Registering URL scheme..."
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -R -f "$APP_PATH" 2>/dev/null || true

# Also set up iTerm as default SSH handler
echo -e "${BLUE}→${NC} Configuring iTerm as SSH handler..."

# Create a defaults write to suggest iTerm for ssh:// URLs
# This doesn't force it but helps

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Installation Complete!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "The iTerm Split-Pane SSH Helper is now installed."
echo ""
echo -e "${YELLOW}One more step:${NC} Set iTerm as your default SSH handler:"
echo -e "  1. Open ${BLUE}iTerm2${NC} → ${BLUE}Settings${NC} (⌘,)"
echo -e "  2. Go to ${BLUE}Profiles${NC} → ${BLUE}General${NC}"
echo -e "  3. Scroll to ${BLUE}URL Schemes${NC}"
echo -e "  4. Check the ${BLUE}ssh${NC} checkbox"
echo ""
echo -e "Now clicking terminal buttons in Topology Creator will:"
echo -e "  • First click: Open new iTerm window with SSH"
echo -e "  • Subsequent clicks: Auto-split pane with SSH"
echo ""
echo -e "${GREEN}Installed to:${NC} $HELPER_DIR"
echo -e "${GREEN}URL Handler:${NC} $APP_PATH"
echo ""







