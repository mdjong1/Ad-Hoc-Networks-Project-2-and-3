import random
import wsnsimpy.wsnsimpy_tk as wsp
from enum import Enum
from Routing.textstyles import TStyle


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
        self.hops = hops

    @classmethod
    def from_other(cls, message):
        """
        :param Message cls: Class
        :param Message message: Message object to clone
        """
        return Message(message.type, message.src, message.seq, message.dest, message.hops + 1)

    def hop(self):
        return Message(self.type, self.src, self.seq, self.dest, self.hops + 1)


class MyNode(wsp.Node):
    """
    Node class that implements all routing behaviour of our node.
    """

    tx_range = 100

    def __init__(self, sim, id, pos):
        """Define variables and initiate node superclass"""
        super().__init__(sim, id, pos)

        # "routing table"
        """
        self.next = None
        self.prev = None
        """
        self.table = {id: {"dest": id, "next": id, "seq": 0, "hops": 0}}

    def init(self):
        super().init()

    def run(self):
        self.scene.nodecolor(self.id, .7, .7, .7)

    def start_send_to(self, dest):
        self.log(f"{TStyle.BLUE}Initiating sending to node {dest}{TStyle.ENDC}")

        yield self.timeout(0.01)  # Very small delay to make sure we're initialised.

        # Node is source, make blue and bold
        self.scene.nodecolor(self.id, 0, 0, 1)
        self.scene.nodewidth(self.id, 2)

        # Make destination red and bold
        self.scene.nodecolor(dest, 1, 0, 0)
        self.scene.nodewidth(dest, 2)

        yield self.timeout(1)
        # Start by sending rreq
        self.send_rreq(Message(MTypes.RREQ, self.id, 0, dest))

    def print_table(self):
        """Pretty print routing table"""
        dashes = 8*5 + 2*4 + 1
        print(f"{TStyle.BOLD}Routing table of node {self.id}{TStyle.ENDC}")
        print('+' + '-' * dashes + '+')  # Row of ---
        print(f"| {'Source':<8}| {'Dest':<8}| {'Next':<8}| {'Seq':<8}| {'Hops':<8}|")
        print('+' + '-' * dashes + '+')  # Row of ---
        for i, row in self.table.items():
            print(f"| {i:<8}| {row['dest']:<8}| {row['next']:<8}| {row['seq']:<8}| {row['hops']:<8}|")
        print('+' + '-' * dashes + '+')  # Row of ---

    def send_rreq(self, msg):
        """
        Broadcast RREQ to all nodes in TX range
        :param Message msg: Message to send
        """
        message = msg.hop()
        self.send(wsp.BROADCAST_ADDR, msg=message)

    def send_rreply(self, msg):
        """
        Send RREP to next link to destination
        :param Message msg: Message to send
        """
        # If we're a node in the path, make node green and bold
        if self.id is not msg.dest:
            self.scene.nodecolor(self.id, 0, .7, 0)
            self.scene.nodewidth(self.id, 2)

        # Forward rreply to previous link in the "routing table"
        message = msg.hop()
        self.send(self.table[msg.dest]["next"], msg=message)

    def start_send_data(self, dest):
        # Remove visual links/pointers
        self.scene.clearlinks()
        seq = 0
        # Infinitely send data with period of 1
        while True:
            yield self.timeout(1)
            self.log(f"{TStyle.PINK}Send data to {dest} with seq {seq}{TStyle.ENDC}")
            message = Message(MTypes.DATA, self.id, seq, dest)
            self.send_data(message)
            seq += 1

    def send_data(self, msg):
        """
        Send data to next link to destination
        :param Message msg: Message to send
        """
        nxt = self.table[msg.dest]["next"]
        self.log(f"Forward data with seq {msg.seq} via {nxt}")
        message = msg.hop()
        self.send(self.table[msg.dest]["next"], msg=message)

    def on_receive(self, sender, msg, **kwargs):
        """
        All responses to a particular cls (`msg`) type
        :param int sender: Sender id
        :param Message msg: Received message
        """

        if msg.type == MTypes.RREQ:
            # If we already received an rreq before, ignore

            if msg.src in self.table:
                if self.table[msg.src]["hops"] > msg.hops:
                    self.table[msg.src] = {"dest": msg.src, "next": sender, "seq": msg.seq, "hops": msg.hops}
                else:
                    return
            else:
                self.table[msg.src] = {"dest": msg.src, "next": sender, "seq": msg.seq, "hops": msg.hops}


            # Draw arrow to parent as defined in __main__
            self.scene.addlink(sender, self.id, "parent")

            # If destination receives the rreq, reply with rreply
            # TODO: check for double RREQs, don't send double RREP
            if self.id is msg.dest:
                self.log(f"{TStyle.LIGHTGREEN}Received RREQ from {msg.src}{TStyle.ENDC}")
                yield self.timeout(3)
                self.log(f"{TStyle.BLUE}Send RREP to {msg.src}{TStyle.ENDC}")
                for link in self.scene.links:
                    self.scene.dellink(link[0], link[1], link[2])
                    self.scene.addlink(link[0], link[1], 'inactive')
                self.send_rreply(Message(MTypes.RREP, self.id, 0, msg.src))

            # If not destination, broadcast rreq again (with random delay)
            else:
                yield self.timeout(delay())
                self.send_rreq(msg)

        elif msg.type == MTypes.RREP:
            """
            self.next = sender
            """
            self.table[msg.src] = {"dest": msg.src, "next": sender, "seq": msg.seq, "hops": msg.hops}

            # Replace link with parent_active version
            try:
                self.scene.dellink(self.id, self.table[msg.src]["next"], 'inactive')
            finally:
                self.scene.addlink(self.id, self.table[msg.src]["next"], 'parent_active')

            # If we're the source, route is established. Start the data sending process
            if self.id is msg.dest:
                self.log(f"{TStyle.LIGHTGREEN}Received RREP from {msg.src}{TStyle.ENDC}")
                yield self.timeout(5)
                self.log(f"{TStyle.BLUE}Start sending data{TStyle.ENDC}")
                # Start new process to send data and keep simulating at the same time
                self.start_process(self.start_send_data(msg.src))
            # If not, forward rreply
            else:
                yield self.timeout(.2)
                self.send_rreply(msg)

        elif msg.type == MTypes.DATA:
            # If not destination, forward data
            if self.id is not msg.dest:
                yield self.timeout(.2)
                self.send_data(msg)
            else:
                self.log(f"{TStyle.LIGHTGREEN}Got data from {msg.src} with seq {msg.seq}{TStyle.ENDC}")


if __name__ == '__main__':
    terrain_size = 600
    terrain_margin = 60
    playfield = terrain_size - 2*terrain_margin

    # Initiate simulator
    simulator = wsp.Simulator(
        until=60,
        timescale=1,
        visual=True,
        terrain_size=(terrain_size, terrain_size),
        title="Static AODV Demo"
    )

    # Define a line style for parent links
    simulator.scene.linestyle("parent", color=(0, .8, 0), arrow="tail", width=2)
    simulator.scene.linestyle("parent_active", color=(0, .8, .8), arrow="tail", width=2)
    simulator.scene.linestyle("inactive", color=(.6, .6, .6), arrow="tail", width=1)

    # Place nodes in grid with random offset
    node_distance = playfield / 6
    for x in range(7):
        for y in range(7):
            px = terrain_margin + x * node_distance + random.uniform(-20, 20)
            py = terrain_margin + y * node_distance + random.uniform(-20, 20)
            node = simulator.add_node(MyNode, (px, py))
            node.tx_range = 95
            node.logging = True

    source_node = simulator.nodes[1]
    # In order to allow a function to use timeouts (delays),
    # it has to be started as a 'process'
    source_node.start_process(source_node.start_send_to(len(simulator.nodes) - 1))
    source_node.print_table()

    # Start simulation
    simulator.run()
