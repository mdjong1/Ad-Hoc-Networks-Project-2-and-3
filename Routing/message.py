from enum import Enum


class MTypes(Enum):
    """Enum for possible message types"""
    RREQ = 1
    RREP = 2
    RERR = 3
    DATA = 4


def delay(a=0.2, b=0.8):
    """Random delay between `a=0.2` and `b=0.8`"""
    return 0.3


class Message:
    """AODV message class"""

    def __init__(self, type, src, seq, dest, hops=0, payload=None):
        """
        :param MTypes type: Message type
        :param int src: Source ID
        :param int seq: Sequence ID
        :param int dest: Destination ID
        :param int hops: Number of hops taken
        """
        # if type not in message_types:
        #     raise Exception(f"Message type ${type} not supported, possible options: ${repr(message_types)}.")
        self.type = type
        self.src = src
        self.seq = seq
        self.dest = dest
        self.hops = hops
        self.payload = payload

    @classmethod
    def from_other(cls, message):
        """
        :param Message cls: Class
        :param Message message: Message object to clone
        """
        return Message(message.type, message.src, message.seq, message.dest, message.hops + 1, message.payload)

    def hop(self):
        return Message(self.type, self.src, self.seq, self.dest, self.hops + 1, self.payload)
