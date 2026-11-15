
import json
import struct


def send_message(sock, message):
    """Serialize a message as JSON and send it with a 4-byte length header."""
    encoded_message = json.dumps(message).encode("utf-8")
    header = struct.pack("!I", len(encoded_message))

    sock.sendall(header + encoded_message)


def receive_exact(sock, num_bytes):
    """Receive exactly the requested number of bytes."""
    data = bytearray()

    # TCP may deliver fewer bytes than requested, so keep reading
    # until the complete message portion has arrived.
    while len(data) < num_bytes:
        chunk = sock.recv(num_bytes - len(data))

        if not chunk:
            raise ConnectionError("Connection closed unexpectedly.")

        data.extend(chunk)

    return bytes(data)


def receive_message(sock):
    """Receive a length-prefixed JSON message."""
    header = receive_exact(sock, 4)
    message_length = struct.unpack("!I", header)[0]

    payload = receive_exact(sock, message_length)

    return json.loads(payload.decode("utf-8"))
