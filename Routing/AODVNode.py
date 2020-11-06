import random
import wsnsimpy.wsnsimpy_tk as wsp
from Routing.message import MTypes, Message
from Routing.textstyles import TStyle
from Routing.demo_control import demo_control_callback

# global demo_control_callback


def delay(a=0.2, b=0.8):
    """Random delay between `a=0.2` and `b=0.8`"""
    return 0.3


class MyNode(wsp.Node):
    """
    Node class that implements all routing behaviour of our node.
    """

    tx_range = 100
    draw_arrows = True

    def __init__(self, sim, id, pos):
        """Define variables and initiate node superclass"""
        super().__init__(sim, id, pos)

        # Routing table
        self.table = {id: {"dest": id, "next": id, "seq": 0, "hops": 0}}
        self.seq = 1

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
        """
        For the first RREQ the seq of the node is taken
        """
        self.send_rreq(Message(MTypes.RREQ, self.id, self.seq, dest))

    def print_table(self):
        """Pretty print routing table"""
        dashes = 8 * 5 + 2 * 4 + 1
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
        if self.id is not msg.dest:
            # If we're a node in the path, make node green and bold
            self.scene.nodecolor(self.id, 0, .7, 0)
            self.scene.nodewidth(self.id, 2)

            # Forward rreply to previous link in the "routing table"
            message = msg.hop()
            self.send(self.table[msg.dest]["next"], msg=message)

            """Check if the path still exists"""
            nxt= self.table[msg.dest]["next"]
            messagesent = 0
            for node in self.neighbors:
                if nxt == node.id:
                    messagesent = 1
                    break

            if messagesent == 0:
                self.log(f"{TStyle.RED}Node {nxt} has disappeared ")
                self.send(wsp.BROADCAST_ADDR, msg=message)

    def start_send_data(self, dest):
        # Remove visual links/pointers
        self.scene.clearlinks()
        """
        First the seq is updated and for each data message a higher seq is taken
        """
        self.seq += 1
        # Send a random amount of data with frequency of 1/s
        for i in range(random.randint(4, 9)):
            yield self.timeout(1)
            self.log(f"{TStyle.PINK}Send data to {dest} with seq {self.seq}{TStyle.ENDC}")
            message = Message(MTypes.DATA, self.id, self.seq, dest)
            self.send_data(message)
            self.seq += 1

        yield self.timeout(2)
        demo_control_callback()

    def send_data(self, msg):
        """
        Send data to next link to destination
        :param Message msg: Message to send
        """
        nxt = self.table[msg.dest]["next"]
        self.log(f"Forward data with seq {msg.seq} via {nxt}")
        message = msg.hop()
        self.send(self.table[msg.dest]["next"], msg=message)

        """Check if the path still exists"""
        messagesent = 0
        for node in self.neighbors:
            if nxt == node.id:
                messagesent = 1
                break

        if messagesent == 0:
            self.log(f"{TStyle.RED}Node {nxt} is disconnected ")

            """
            Message type = RRER
            Src = destination, this will be used to restart the RREQ to this destination
            seq = making it 0 ensures that no table will be updated
            Dest = the source of the data message
            """
            self.send_rrer(Message(MTypes.RRER, msg.dest, 0, msg.src))

    def send_rrer(self, msg):

        if self.id is not msg.dest:
            # If we're a node in the path, make node green and bold
            self.scene.nodecolor(self.id, .7, 0, 0)
            self.scene.nodewidth(self.id, 2)

            self.log(f"{TStyle.BLUE}Sending RRER{TStyle.ENDC}")
            # Forward rreply to previous link in the "routing table"
            nxt = self.table[msg.dest]["next"]
            message = msg.hop()
            self.send(nxt, msg=message)

            """Check if the path still exists"""

            messagesent = 0
            for node in self.neighbors:
                if nxt == node.id:
                    messagesent = 1
                    break

            if messagesent == 0:
                nxt = self.table[msg.dest]["next"]
                self.log(f"{TStyle.RED}Node {nxt} is disconnected ")
                self.send(wsp.BROADCAST_ADDR, msg=message)

    def on_receive(self, sender, msg, **kwargs):
        """
        All responses to a particular cls (`msg`) type
        :param int sender: Sender id
        :param Message msg: Received message
        """

        if msg.type == MTypes.RREQ:
            # If we already received an rreq before, ignore
            if msg.src in self.table:
                if self.table[msg.src]["seq"] < msg.seq:
                    self.table[msg.src] = {"dest": msg.src, "next": sender, "seq": msg.seq, "hops": msg.hops}
                elif self.table[msg.src]["seq"] == msg.seq:
                    if self.table[msg.src]["hops"] > msg.hops:
                        self.table[msg.src] = {"dest": msg.src, "next": sender, "seq": msg.seq, "hops": msg.hops}
                    else:
                        return
                else:
                    return
            else:
                self.table[msg.src] = {"dest": msg.src, "next": sender, "seq": msg.seq, "hops": msg.hops}

            # Draw arrow to parent as defined in __main__
            if self.draw_arrows:
                self.scene.addlink(sender, self.id, "parent")

            # If destination receives the rreq, reply with rreply

            if self.id is msg.dest:
                self.log(f"{TStyle.LIGHTGREEN}Received RREQ from {msg.src}{TStyle.ENDC}")
                yield self.timeout(3)
                self.log(f"{TStyle.BLUE}Send RREP to {msg.src}{TStyle.ENDC}")
                """
                The seq is updated with 10 when DEST receives a RREQ
                """
                self.seq += 10
                self.send_rreply(Message(MTypes.RREP, self.id, self.seq, msg.src))

            # If not destination, broadcast rreq again (with random delay)
            else:
                yield self.timeout(delay())
                self.send_rreq(msg)

        elif msg.type == MTypes.RREP:
            """
            self.next = sender
             """
            if msg.src in self.table:
                if self.table[msg.src]["seq"] < msg.seq:
                    self.table[msg.src] = {"dest": msg.src, "next": sender, "seq": msg.seq, "hops": msg.hops}
                elif self.table[msg.src]["seq"] == msg.seq:
                    if self.table[msg.src]["hops"] > msg.hops:
                        self.table[msg.src] = {"dest": msg.src, "next": sender, "seq": msg.seq, "hops": msg.hops}
                    else:
                        return
                else:
                    return
            else:
                self.table[msg.src] = {"dest": msg.src, "next": sender, "seq": msg.seq, "hops": msg.hops}

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

        elif msg.type == MTypes.RERR:

            if self.id is msg.dest:
                self.log(f"{TStyle.LIGHTGREEN}Received RRER from {msg.src}{TStyle.ENDC}")
                yield self.timeout(5)
                self.log(f"{TStyle.BLUE}Restart sending RREQ{TStyle.ENDC}")
                # broadcast a RREQ to find a new path
                """
                The seq is updated by 2 when starting a new RREQ
                """
                self.seq += 2
                self.send_rreq(Message(MTypes.RREQ, self.id, self.seq, msg.dest))
                self.start_process(self.start_send_data(msg.src))
            # If not, forward rreply
            else:
                yield self.timeout(.2)
                self.send_rrer(msg)
