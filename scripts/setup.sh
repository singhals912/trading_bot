#!/bin/bash

echo "Disabling system sleep..."
sudo pmset -a sleep 0
sudo pmset -a disablesleep 1

echo "Creating LaunchDaemon plist..."
cat <<EOF | sudo tee /Library/LaunchDaemons/com.tradingbot.plist > /dev/null
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.tradingbot</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/$(whoami)/trading_bot/venv/bin/python</string>
        <string>/Users/$(whoami)/trading_bot/main.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/$(whoami)/trading_bot/logs/stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/$(whoami)/trading_bot/logs/stderr.log</string>
</dict>
</plist>
EOF

echo "Loading LaunchDaemon..."
sudo launchctl load /Library/LaunchDaemons/com.tradingbot.plist
