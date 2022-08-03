# ESPNow Utilities
A collection of small utilities for use with espnow and wifi on micropython

- `lib/wifi.py`: A small module to bulletproof initialising wifi on ESP32 and ESP8266 devices.

```
import wifi

sta, ap = wifi.reset()   # Reset and set to STA_IF on and disconnected, AP off, channel=1
sta, ap = wifi.reset(sta=True, ap=True, channel=6)   # STA_IF on and disconnected, AP on, channel=6
```

- `lib/scan_for_peer.py`: Scan channels to find an ESPNow peer.
- `lib/lazyespnow.py`: LazyESPNow() extends ESPNow class to catch and fix most common errors.
- `lib/ntp.py`: Set the time from an NTP server over wifi.
- `lib/timer.py`: A useful collection of easy to user python timer objects.
- `lib/echo.py`: A simple ESPNow server that echos messages back to the sender.
