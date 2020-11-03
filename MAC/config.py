BYTE_TRANSMISSION_TIME = 0.02  # second(s)
TX_CIRCLE_DELTA = 50  # how close are subsequent TX circles to one another

MIN_BACKOFF_TIME = 2  # # slots
MAX_BACKOFF_TIME = 64  # # slots


DATA_LENGTH = {
    "ACK": 8,
    "DS": 30,
    "CTS": 30,
    "RTS": 30,
    "RRTS": 30,
}

# One time slot is considered the time a CTS packet can be send
SLOT_TIME = (BYTE_TRANSMISSION_TIME * DATA_LENGTH["CTS"])
