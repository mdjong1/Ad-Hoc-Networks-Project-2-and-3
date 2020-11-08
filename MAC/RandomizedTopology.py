import math
import random

from MacawNode import MacawNode
import wsnsimpy.wsnsimpy_tk as wsp

PACKET_SIZE = 256
TX_RANGE = 100
NUM_SENDERS = 5
NODE_SPACING = 50
NUM_NODES = 30
GRID_BOUNDS = [50, 50, 600, 600]


class RandomizedTopology:

    def __init__(self):
        self.nodes = []

    def set_nodes(self):
        for x in range(NUM_NODES):
            self.nodes.append(simulator.add_node(MacawNode, self.get_pos()))

        for node in self.nodes:
            node.tx_range = TX_RANGE

    def get_pos(self):
        pos = (
            random.randint(GRID_BOUNDS[0], GRID_BOUNDS[2]),
            random.randint(GRID_BOUNDS[0], GRID_BOUNDS[2])
        )

        for node in self.nodes:
            if abs(node.pos[0] - pos[0]) < NODE_SPACING and abs(node.pos[1] - pos[1]) < NODE_SPACING:
                return self.get_pos()

        return pos

    def get_receiver(self, sender):
        # Ensure receiver != sender
        possible_receiver = self.nodes[random.choice([i for i in range(0, NUM_NODES - 1) if i != sender.id])]

        # Ensure receiver is within range of sender (Pythagoras)
        if math.sqrt((sender.pos[0] - possible_receiver.pos[0]) ** 2 + (sender.pos[1] - possible_receiver.pos[1]) ** 2) > TX_RANGE:
            return self.get_receiver(sender)

        else:
            return possible_receiver

    def run(self):
        for cluster in range(NUM_SENDERS):
            sender = self.nodes[random.randint(0, NUM_NODES - 1)]

            receiver = self.get_receiver(sender)

            sender.add_data(PACKET_SIZE, receiver, time_offset=random.randint(0, int(NUM_SENDERS / 2)))


if __name__ == '__main__':
    simulator = wsp.Simulator(
        until=60,
        timescale=1,
        visual=True,
        terrain_size=(650, 650),
        title="MACAW Randomized Topology Demo"
    )

    topology = RandomizedTopology()
    topology.set_nodes()
    topology.run()

    simulator.run()
