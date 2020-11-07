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
    cancel_data_transfer = False

    def __init__(self, sim, id, pos):
        """Define variables and initiate node superclass"""
        super().__init__(sim, id, pos)

        # Routing table,
        # the seq in the table entry to itself is very high
        self.table = {id: {"dest": id, "next": id, "seq": 1000, "hops": 0}}
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
        if dest in self.table:
            self.log(f"{TStyle.LIGHTGREEN}Route to {dest} found in routing table{TStyle.ENDC}")
            self.log(f"{TStyle.BLUE}Start sending data{TStyle.ENDC}")
            # Start new process to send data and keep simulating at the same time
            self.start_process(self.start_send_data(dest))
        else:
            msg = Message(MTypes.RREQ, self.id, self.seq, dest)
            self.send_rreq(msg)
        # For the first RREQ the seq of the node is taken

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

    def next_reachable(self, msg):
        """
        Check if the path still exists and send RERR if not
        :param Message msg: The message to check the path for
        :return: Whether path is available
        """
        reachable = False
        next_hop = None
        # If the destination is not in our table (anymore), send
        if msg.dest in self.table:
            next_hop = self.table[msg.dest]["next"]
            for node in self.neighbors:
                if next_hop == node.id:
                    reachable = True
                    break
            if not reachable:
                self.log(f"{TStyle.RED}Node {next_hop} is cannot be reached{TStyle.ENDC}")
        else:
            self.log(f"{TStyle.RED}Node {msg.dest} not in routing table{TStyle.ENDC}")

        if not reachable:
            # Message type = RERR
            # Src = destination, this will be used to restart the RREQ to this destination
            # seq = making it 0 ensures that no table will be updated
            # Dest = the source of the data message
            self.send_rerr(
                Message(MTypes.RERR, self.id, 0, msg.src, payload={"orig_dest": msg.dest, "broken_link": next_hop})
            )

        return reachable

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
            if self.id is not msg.src:
                # If we're a node in the path, make node cyan and bold
                self.scene.nodecolor(self.id, 0, .7, .9)
                self.scene.nodewidth(self.id, 2)

            # Forward RREP to previous link in the "routing table"
            if self.next_reachable(msg):
                message = msg.hop()
                self.send(self.table[msg.dest]["next"], msg=message)

    def start_send_data(self, dest):
        # Remove visual links/pointers
        self.scene.clearlinks()
        # First the seq is updated and for each data message a higher seq is taken
        self.seq += 1
        # Send a random amount of data with frequency of 1/s
        for i in range(random.randint(4, 9)):
            yield self.timeout(1)
            if self.cancel_data_transfer:
                self.log("Canceled data transfer")
                break
            self.log(f"{TStyle.PINK}Send data to {dest} with seq {self.seq}{TStyle.ENDC}")
            message = Message(MTypes.DATA, self.id, self.seq, dest)
            self.send_data(message)
            self.seq += 1

        if self.cancel_data_transfer:
            self.cancel_data_transfer = False
        else:
            yield self.timeout(2)
            demo_control_callback()

    def send_data(self, msg):
        """
        Send data to next link to destination
        :param Message msg: Message to send
        """
        if self.next_reachable(msg):
            self.log(f"Forward data with seq {msg.seq} via {self.table[msg.dest]['next']}")
            message = msg.hop()
            self.send(self.table[msg.dest]["next"], msg=message)

    def send_rerr(self, msg):

        if self.id is not msg.dest:
            # If we're a node in the path, make node orange and bold
            self.scene.nodecolor(self.id, 1, .7, 0)
            self.scene.nodewidth(self.id, 2)

            self.log(f"{TStyle.BLUE}Sending RERR{TStyle.ENDC}")
            # Forward rreply to previous link in the "routing table"
            nxt = self.table[msg.dest]["next"]
            message = msg.hop()
            self.send(nxt, msg=message)

            # Check if the path still exists

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
            # If this destination is new, or this msg is newer, or has a lower hop count, save
            if msg.src not in self.table or \
               msg.seq > self.table[msg.src]["seq"] or \
               (self.table[msg.src]["seq"] == msg.seq and self.table[msg.src]["hops"] > msg.hops):

                self.table[msg.src] = {"dest": msg.src, "next": sender, "seq": msg.seq, "hops": msg.hops}
            # Else, do nothing
            else:
                return

            # Draw arrow to parent as defined in __main__
            if self.draw_arrows:
                self.scene.addlink(sender, self.id, "parent")

            # If destination receives the RREQ, reply with RREP
            if self.id is msg.dest:
                self.log(f"{TStyle.LIGHTGREEN}Received RREQ from {msg.src}{TStyle.ENDC}")
                yield self.timeout(3)
                self.log(f"{TStyle.BLUE}Send RREP to {msg.src}{TStyle.ENDC}")
                # The seq is updated with 10 when DEST receives a RREQ
                self.seq += 10
                self.send_rreply(Message(MTypes.RREP, self.id, self.seq, msg.src))
            # If this node has the route, reply with RREP
            elif msg.dest in self.table:
                self.log(f"{TStyle.LIGHTGREEN}Node {self.id} has route to {msg.dest}{TStyle.ENDC}")
                yield self.timeout(1)
                self.log(f"{TStyle.BLUE}Send RREP to {msg.src}{TStyle.ENDC}")
                # The seq is updated with 10 when DEST receives a RREQ
                self.seq += 10
                self.send_rreply(Message(MTypes.RREP, self.id, self.seq, msg.src))

            # If not destination, broadcast rreq again (with random delay)
            else:
                yield self.timeout(delay())
                self.send_rreq(msg)

        elif msg.type == MTypes.RREP:
            # If this destination is new, or this msg is newer, or has a lower hop count, save
            if msg.src not in self.table or \
                    msg.seq > self.table[msg.src]["seq"] or \
                    (self.table[msg.src]["seq"] == msg.seq and self.table[msg.src]["hops"] > msg.hops):

                self.table[msg.src] = {"dest": msg.src, "next": sender, "seq": msg.seq, "hops": msg.hops}
            # Else, do nothing
            else:
                return

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
            # If we get notified that our destination is unreachable
            if self.id is msg.dest:
                # Stop the current data transfer
                self.cancel_data_transfer = True
                self.log(f"{TStyle.LIGHTGREEN}Received RERR for {msg.payload['orig_dest']} from {msg.src}{TStyle.ENDC}")
                yield self.timeout(3)
                self.log(f"{TStyle.BLUE}Restart sending RREQ for {msg.payload['orig_dest']}{TStyle.ENDC}")
                # Broadcast a RREQ to find a new path to orig_dest
                # The seq is updated by 2 when starting a new RREQ
                self.seq += 2
                self.send_rreq(Message(MTypes.RREQ, self.id, self.seq, msg.payload["orig_dest"]))
                # Restart data sending is automatically triggered when the RREQ comes back, following not necessary
                # self.start_process(self.start_send_data(msg.payload["orig_dest"]))
            # If not, forward RERR
            else:
                yield self.timeout(.2)
                # Remove original destination from the routing table
                if msg.payload["orig_dest"] in self.table:
                    del self.table[msg.payload["orig_dest"]]
                self.send_rerr(msg)
