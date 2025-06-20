
#!/bin/bash

# Keep Mac awake
caffeinate -d -i -s &

# Setup LaunchAgent for auto-start
cat > ~/Library/LaunchAgents/com.trading.bot.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" 
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.trading.bot</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>$HOME/trading_bot/main.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
        <key>Crashed</key>
        <true/>
    </dict>
    <key>StandardOutPath</key>
    <string>$HOME/trading_bot/logs/stdout.log</string>
    <key>StandardErrorPath</key>
    <string>$HOME/trading_bot/logs/stderr.log</string>
</dict>
</plist>
EOF

launchctl load ~/Library/LaunchAgents/com.trading.bot.plist

# Setup monitoring
pip install psutil schedule twilio

echo "Local environment setup complete"
