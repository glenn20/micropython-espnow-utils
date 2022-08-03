import espnow

enow = espnow.ESPNow()

def echo_server():
    peers = []
    for peer, msg in enow:
        if peer is None:
            return
        if peer not in peers:
            peers.append(peer)
            try:
                enow.add_peer(peer)
            except OSError:
                pass

        #  Echo the MAC and message back to the sender
        if not enow.send(peer, msg):
            print("ERROR: send() failed to", peer)
            return

        if msg == b"!done":
            return

def echo(peer, msg):
    try:
        enow.add_peer(peer)
    except OSError:
        pass
    if not enow.send(peer, msg):
        print("ERROR: Send failed.")
        return False
    p2, msg2 = enow.irecv()
    if not msg2:
        print("Timeout")
        return False
    print("OK" if msg2 == msg else "ERROR: Received != Sent")
    return msg2 == msg

def echo_client(e, peer, msglens):
    import random
    for msglen in msglens:
        msg = bytearray(msglen)
        if msglen > 0:
            msg[0] = ord(b'_')  # Random message must not start with '!'
        for i in range(1, msglen):
            msg[i] = random.getrandbits(8)
        echo_test(e, peer, msg)
