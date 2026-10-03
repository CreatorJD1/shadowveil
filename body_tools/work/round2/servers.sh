cd /workspace/r2tree && setsid nohup python3 -m http.server 8770 --bind 127.0.0.1 > /tmp/http8770.log 2>&1 &
cd /workspace/r2stage && setsid nohup python3 -m http.server 8771 --bind 127.0.0.1 > /tmp/http8771.log 2>&1 &
