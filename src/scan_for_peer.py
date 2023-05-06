import sys, wifi

def scan_for_peer(enow, peer, retries=3):
    """Scan the wifi channels to find the given peer device.

    If the peer is found, the channel will be printed and the channel number
    returned.
    Will:
        - disconnect the STA_IF if it is connected();
        - scan using the STA_IF;
        - turn off the AP_IF when finished (on esp8266); and
        - leave the STA_IF running on the channel of the peer.

    Args:
        enow: An ESPNow class instance.
        peer (bytes): The MAC address of the peer device to find.
        retries (int, optional):
            Number of times to attempt to send for each channel. Defaults to 3.

    Returns:
        int: The channel number of the peer (or 0 if not found)
    """
    try:
        enow.add_peer(peer)
    except OSError:
        pass
    for channel in range(1, 14):
        wifi.channel(channel)
        for _ in range(retries):
            if enow.send(peer, b'ping'):
                print(f"Found peer {peer} on channel {channel}.")
                return channel
    return 0
