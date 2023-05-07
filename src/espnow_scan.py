import sys
import network
import espnow

sta, ap = (network.WLAN(i) for i in (network.STA_IF, network.AP_IF))

def set_channel(channel):
    if sta.isconnected():
        raise OSError("can not set channel when connected to wifi network.")
    if ap.isconnected():
        raise OSError("can not set channel when clients are connected to AP.")
    if sta.active() and sys.platform != "esp8266":
        sta.config(channel=channel)  # On ESP32 use STA interface
        return sta.config("channel")
    else:
        # On ESP8266, use the AP interface to set the channel of the STA interface
        ap_save = ap.active()
        ap.active(True)
        ap.config(channel=channel)
        ap.active(ap_save)
        return ap.config("channel")


def scan(peer, retries=5):
    """Scan the wifi channels to find the given espnow peer device.

    If the peer is found, the channel will be printed and the channel number
    returned.
    Will:
        - scan using the STA_IF;
        - turn off the AP_IF when finished (on esp8266); and
        - leave the STA_IF running on the selected channel of the peer.

    Args:
        peer (bytes): The MAC address of the peer device to find.
        retries (int, optional):
            Number of times to attempt to send for each channel. Defaults to 5.

    Returns:
        int: The channel number of the peer (or 0 if not found)
    """
    enow = espnow.ESPNow()
    enow.active(True)
    try:
        enow.add_peer(peer)  # If user has not already registered peer
    except OSError:
        pass
    found = []
    for channel in range(1, 15):
        set_channel(channel)
        for _ in range(retries):
            if enow.send(peer, b'ping'):
                found.append(channel)
                print(f"Found peer {peer} on channel {channel}.")
                break
                # return channel
    if not found:
        return 0
    # Because of channel cross-talk we expect more than one channel to be found
    # If 3 channels found, select the middle one
    # If 2 channels found: select first one if it is channel 1 else second
    # If 1 channels found, select it
    count = len(found)
    index = 0 if count == 1 or (count == 2 and found[0] == 1) else 1
    channel = found[index]
    print(f"Setting wifi channel to {channel}")
    set_channel(channel)
    return channel
