# """
# wifi.py: Useful functions for setting up wifi on ESP32 and ESP8266 devices

# These functions are designed to robustly and reliably account for differences
# between esp8266 and esp32 devices and to ensure the wifi is always in a fully
# known state (even after soft_reset).

# Examples:

#     import wifi

#     # Reset wifi to know state (STA is disconnected)
#     sta, ap = wifi.reset()               # STA on, AP off, channel=1
#     sta, ap = wifi.reset(sta=True, ap=True, channel=5)  # STA on, AP on, channel=5
#     sta, ap = wifi.reset(False, False)   # STA off, AP off, channel=1
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
import esp


class TimeoutError(Exception):
    pass


this = sys.modules[__name__]  # A reference to this module

is_esp8266 = sys.platform == "esp8266"
wlans = [network.WLAN(w) for w in (network.STA_IF, network.AP_IF)]
sta, ap = wlans
_sta, _ap = wlans
timeout = 20  # (seconds) timeout on connect()
default_channel = 1
if is_esp8266:
    default_ps_mode = esp.SLEEP_NONE
else:
    default_ps_mode = network.WIFI_PS_NONE
try:
    default_protocol = network.MODE_11B | network.MODE_11G | network.MODE_11N
except AttributeError:
    default_protocol = None


def channel(channel=0):
    if channel == 0:
        return _ap.config("channel")
    if _sta.isconnected():
        raise OSError("can not set channel when connected to wifi network.")
    if _ap.isconnected():
        raise OSError("can not set channel when clients are connected to AP.")
    if _sta.active() and not is_esp8266:
        _sta.config(channel=channel)  # On ESP32 use STA interface
        return _sta.config("channel")
    else:
        # On ESP8266, use the AP interface to set the channel
        ap_save = _ap.active()
        _ap.active(True)
        _ap.config(channel=channel)  # Catch exceptions so we can reset AP_IF
        _ap.active(ap_save)
        return _ap.config("channel")


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
    _sta.active(True)
    disconnect()
    _sta.connect(*args, **kwargs)
    wait_for(lambda: _sta.isconnected())
    ssid, chan = _sta.config("essid"), channel()
    print('Connected to "{}" on wifi channel {}'.format(ssid, chan))


def reset(
    sta=True,
    ap=False,
    channel=default_channel,
    ps_mode=default_ps_mode,
    protocol=default_protocol,
):
    "Reset wifi to STA_IF on, AP_IF off, channel=1 and disconnected"
    _sta.active(False)  # Force into know state by turning off radio
    _ap.active(False)
    _sta.active(sta)  # Now set to requested state
    _ap.active(ap)
    if sta:
        disconnect()  # For ESP8266
    if sta:  # Not necessary here - but is expected by users
        if is_esp8266:
            esp.sleep_type(ps_mode)
        else:
            _sta.config(ps_mode=ps_mode)
    try:
        wlan = _sta if sta else _ap if ap else None
        if wlan and (protocol is not None):
            wlan.config(protocol=protocol)
    except (ValueError, RuntimeError):
        pass
    this.channel(channel)
    return _sta, _ap


def status():
    from binascii import hexlify

    for name, w in (("STA", _sta), ("AP", _ap)):
        active = "on," if w.active() else "off,"
        mac = w.config("mac")
        hex = hexlify(mac, ":").decode()
        print("{:3s}: {:4s} mac= {} ({})".format(name, active, hex, mac))
    if _sta.isconnected():
        print("     connected:", _sta.config("essid"), end="")
    else:
        print("     disconnected", end="")
    print(", channel={:d}".format(_ap.config("channel")), end="")
    try:
        if is_esp8266:
            names = {0: "SLEEP_NONE", 1: "SLEEP_LIGHT", 2: "SLEEP_MODEM"}
            ps_mode = esp.sleep_type()
        else:
            names = {0: "WIFI_PS_NONE", 1: "WIFI_PS_MIN_MODEM", 2: "WIFI_PS_MAX_MODEM"}
            ps_mode = _sta.config("ps_mode")
        print(", ps_mode={:d} ({})".format(ps_mode, names[ps_mode]), end="")
    except ValueError:
        pass
    try:
        names = ("MODE_11B", "MODE_11G", "MODE_11N", "MODE_LR")
        protocol = _sta.config("protocol")
        p = "|".join((x for x in names if protocol & getattr(network, x)))
        print(", protocol={:d} ({})".format(protocol, p), end="")
    except ValueError:
        pass
    print()
    if _sta.isconnected():
        print("     ifconfig:", _sta.ifconfig())
