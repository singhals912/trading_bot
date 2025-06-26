#!/bin/bash
# Auto-restart Pinggy every 50 minutes

while true; do
    echo "🚀 Starting Pinggy tunnel at $(date)"
    
    # Start tunnel and capture URL
    ssh -p 443 -o StrictHostKeyChecking=no \
        -R 0:localhost:8080 qr@a.pinggy.io > pinggy_output.log 2>&1 &
    PINGGY_PID=$!
    
    sleep 10
    
    # Extract and save URL
    URL=$(grep -o 'https://[^[:space:]]*\.a\.pinggy\.io' pinggy_output.log | head -1)
    if [ ! -z "$URL" ]; then
        echo "✅ Current URL: $URL"
        echo "$URL" > current_pinggy_url.txt
        echo "$(date): $URL" >> pinggy_urls.log
    fi
    
    # Wait 50 minutes, then restart
    echo "⏰ Restarting in 50 minutes..."
    sleep 3000  # 50 minutes
    
    kill $PINGGY_PID 2>/dev/null
    sleep 5
done
