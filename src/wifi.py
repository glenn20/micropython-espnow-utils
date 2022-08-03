# """
# wifi.py: Useful functions for setting up wifi on ESP32 and ESP8266 devices

# These functions are designed to robustly and reliably account for differences
# between esp8266 and esp32 devices and to ensure the wifi is always in a fully
# known state (even after soft_reset).

# Examples:

#     import wifi

#     # Reset wifi to know state (STA is disconnected)
#     sta, ap = wifi.reset()               # STA on, AP off, channel=1
#     sta, ap = wifi.reset(True, True, 5)  # STA on, AP on, channel=5
#     sta, ap = wifi.reset(False, False)   # STA on, AP on, channel=1
#     sta, ap = wifi.reset(ap=True)        # STA on, AP on, channel=1
#     sta, ap = wifi.reset(channel=11)     # STA on, AP off, channel=11

#     # Set/get the channel
#     wifi.channel(11)
#     print(wifi.channel())

#     # Connect/disconnect from a wifi network
#     wifi.connect("ssid", "password")
#     wifi.connect()                       # Reconnect to last wifi network
#     wifi.disconnect()                    # Disconnect from wifi network

#     # Print verbose details of the device wifi config
#     wifi.status()

# Config:

#     # Power save mode used whenever connected() - default is WIFI_PS_NONE
#     wifi.ps_mode = network.WIFI_PS_MIN_MODEM
#     wifi.timeout = 30             # Timeout for connect to network (seconds)
#     wifi.sta    # The STA_IF wlan interface
#     wifi.ap     # The AP_IF wlan interface
# """

import sys
import time
import network


class TimeoutError(Exception):
    pass


is_esp8266 = sys.platform == "esp8266"
wlans = [network.WLAN(w) for w in (network.STA_IF, network.AP_IF)]
_sta, _ap = wlans
timeout = 20  # (seconds) timeout on connect()
ps_mode = None if is_esp8266 else network.WIFI_PS_NONE
protocol = None if is_esp8266 else network.MODE_11B | network.MODE_11G | network.MODE_11N


def channel(channel=0):
    if channel == 0:
        return _ap.config("channel")
    if _sta.isconnected():
        print("Error: can not set channel when connected to wifi network.")
    if _ap.isconnected():
        print("Error: can not set channel when clients are connected to AP.")
    if not is_esp8266:
        _sta.config(channel=channel)  # On ESP32 use STA interface
        return _sta.config("channel")
    else:
        # On ESP8266, use the AP interface to set the channel
        ap_save = _ap.active()
        _ap.active(True)
        _ap.config(channel=channel)  # Catch exceptions so we can reset AP_IF
        _ap.active(ap_save)
        return _ap.config("channel")


set_channel = channel


def wait_for(fun, timeout=timeout):
    start = time.time()
    while not fun():
        if time.time() - start > timeout:
            raise TimeoutError()
        time.sleep(0.1)


def disconnect():
    _sta.disconnect()
    wait_for(lambda: not _sta.isconnected(), 5)


def connect(*args, **kwargs):
    if _sta.isconnected():
        disconnect()
    _sta.connect(*args, **kwargs)
    wait_for(lambda: _sta.isconnected())
    ssid, chan = _sta.config("ssid"), channel()
    print('Connected to "{}" on wifi channel {}'.format(ssid, chan))
    if not is_esp8266:   # Set preferred power saving mode after connect
        _sta.config(ps_mode=ps_mode)


def reset(sta=True, ap=False, channel=1):
    "Reset wifi to STA_IF on, AP_IF off, channel=1 and disconnected"
    _sta.active(False)  # Force into know state by turning off radio
    _ap.active(False)
    _sta.active(sta)  # Now set to requested state
    _ap.active(ap)
    disconnect()  # For ESP8266
    if not is_esp8266:
        _sta.config(protocol=protocol)
    set_channel(channel)
    return _sta, _ap


def status():
    from binascii import hexlify

    for name, w in (("STA", _sta), ("AP", _ap)):
        active = "on," if w.active() else "off,"
        mac = w.config("mac")
        hex = hexlify(mac, ":").decode()
        print("{:3s}: {:4s} mac= {} ({})".format(name, active, hex, mac))
    connected = ("connected: " + _sta.config("ssid")) if _sta.isconnected() else "disconnected"
    channel = _ap.config("channel")
    print("     {}, channel={:d}".format(connected, channel), end="")
    if not is_esp8266:
        ps_mode = _sta.config("ps_mode")
        protocol = _sta.config("protocol")
        print(", ps_mode={:d}, protocol={:d}".format(ps_mode, protocol))
    else:
        print()
    if _sta.isconnected():
        print("     ifconfig:", _sta.ifconfig())
