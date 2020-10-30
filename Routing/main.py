import random
import wsnsimpy.wsnsimpy_tk as wsp
from enum import Enum

SOURCE = 1
DEST   = 99


class MTypes(Enum):
    """Enum for possible message types"""
    RREQ = 1
    RREP = 2
    RERR = 3
    DATA = 4


def delay(a=0.2, b=0.8):
    """Random delay between `a=0.2` and `b=0.8`"""
    return random.uniform(a, b)


class Message:
    """AODV message class"""
    def __init__(self, type, src, seq, dest, hops=0):
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
        self.hops = 0

    @classmethod
    def from_other(cls):
        """
        :param Message cls: Message object to clone
        """
        return Message(cls.type, cls.src, cls.seq, cls.dest, cls.hops + 1)


class MyNode(wsp.Node):
    """
    Node class that implements all routing behaviour of our node.
    """

    tx_range = 100

    def __init__(self, sim, id, pos):
        """Define variables and initiate node superclass"""
        super().__init__(sim, id, pos)

        # "routing table"
        self.next = None
        self.prev = None

    def init(self):
        super().init()

    def run(self):
        # If node is source, make blue and bold
        if self.id is SOURCE:
            self.scene.nodecolor(self.id,0,0,1)
            self.scene.nodewidth(self.id,2)
            yield self.timeout(1)
            # Start by sending rreq
            self.send_rreq(self.id)
        # If node is destination, make red and bold
        elif self.id is DEST:
            self.scene.nodecolor(self.id,1,0,0)
            self.scene.nodewidth(self.id,2)
        # Else, make gray
        else:
            self.scene.nodecolor(self.id,.7,.7,.7)

    def send_rreq(self, src):
        """
        Broadcast rreq to all nodes in TX range
        :param int src: Id of the node that sends the rreq
        """
        message = Message(MTypes.RREQ, src, 0, DEST)
        self.send(wsp.BROADCAST_ADDR, msg=message, src=src)

    def send_rreply(self, src):
        # If we're a node in the path, make node green and bold
        if self.id is not DEST:
            self.scene.nodecolor(self.id,0,.7,0)
            self.scene.nodewidth(self.id,2)
        # Forward rreply to previous link in the "routing table"
        message = Message(MTypes.RREP, src, 0, SOURCE)
        self.send(self.prev, msg=message, src=src)

    def start_send_data(self):
        # Remove visual links/pointers
        self.scene.clearlinks()
        seq = 0
        # Infinitely send data with period of 1
        while True:
            yield self.timeout(1)
            self.log(f"Send data to {DEST} with seq {seq}")
            self.send_data(self.id, seq)
            seq += 1

    def send_data(self, src, seq):
        self.log(f"Forward data with seq {seq} via {self.next}")
        message = Message(MTypes.DATA, src, seq, DEST)
        self.send(self.next, msg=message, src=src, seq=seq)

    def on_receive(self, sender, msg, src, **kwargs):
        """
        All responses to a particular cls (`msg`) type
        :param int sender: Sender id
        :param Message msg: Received message
        """

        if msg.type == MTypes.RREQ:
            # If we already received an rreq before, ignore
            if self.prev is not None: return

            # Make prev pointer to sender.
            self.prev = sender
            # Draw arrow to parent as defined in __main__
            self.scene.addlink(sender,self.id,"parent")


            # If destination receives the rreq, reply with rreply
            if self.id is msg.dest:
                self.log(f"Receive RREQ from {src}")
                yield self.timeout(5)
                self.log(f"Send RREP to {src}")
                self.send_rreply(self.id)
            # If not destination, broadcast rreq again (with random delay)
            else:
                yield self.timeout(delay())
                self.send_rreq(src)

        elif msg.type == MTypes.RREP:
            self.next = sender
            # If we're the source, route is established. Start the data sending process
            if self.id is msg.dest:
                self.log(f"Receive RREP from {src}")
                yield self.timeout(5)
                self.log("Start sending data")
                # Start new process to send data and keep simulating at the same time
                self.start_process(self.start_send_data())
            # If not, forward rreply
            else:
                yield self.timeout(.2)
                self.send_rreply(src)

        elif msg.type == MTypes.DATA:
            # If not destination, forward data
            if self.id is not msg.dest:
                yield self.timeout(.2)
                self.send_data(src,**kwargs)
            else:
                seq = msg.seq
                self.log(f"Got data from {src} with seq {seq}")


if __name__ == '__main__':
    # Initiate simulator
    simulator = wsp.Simulator(
        until=60,
        timescale=1,
        visual=True,
        terrain_size=(700, 700),
        title="Static AODV Demo"
    )

    # Define a line style for parent links
    simulator.scene.linestyle("parent", color=(0, .8, 0), arrow="tail", width=2)

    # Place nodes over 100x100 grids
    for x in range(10):
        for y in range(10):
            px = 50 + x * 60 + random.uniform(-20, 20)
            py = 50 + y * 60 + random.uniform(-20, 20)
            node = simulator.add_node(MyNode, (px, py))
            node.tx_range = 75
            node.logging = True

    # Start simulation
    simulator.run()
