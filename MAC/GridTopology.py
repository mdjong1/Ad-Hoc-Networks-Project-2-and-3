import math
import random

from MacawNode import MacawNode
import wsnsimpy.wsnsimpy_tk as wsp

TX_RANGE = 100
NUM_SENDERS = 3
NODE_SPACING = 60
GRID_BOUNDS = [50, 50, 600, 600]


class GridTopology:

    def __init__(self):
        self.nodes = []

    def set_nodes(self):
        for x in range(GRID_BOUNDS[0], GRID_BOUNDS[2], NODE_SPACING):
            for y in range(GRID_BOUNDS[1], GRID_BOUNDS[3], NODE_SPACING):
                print(x, y)
                self.nodes.append(simulator.add_node(MacawNode, (x, y)))

        for node in self.nodes:
            node.tx_range = TX_RANGE

    def get_receiver(self, sender):
        # Ensure receiver != sender
        possible_receiver = self.nodes[random.choice([i for i in range(0, len(self.nodes) - 1) if i != sender.id])]

        # Ensure receiver is within range of sender (Pythagoras)
        if math.sqrt((sender.pos[0] - possible_receiver.pos[0]) ** 2 + (sender.pos[1] - possible_receiver.pos[1]) ** 2) > TX_RANGE:
            return self.get_receiver(sender)

        else:
            return possible_receiver.id

    def run(self):
        for cluster in range(NUM_SENDERS):
            print(len(self.nodes))
            sender = self.nodes[random.randint(0, len(self.nodes) - 1)]

            receiver = self.get_receiver(sender)

            sender.send_rts(receiver)


if __name__ == '__main__':
    simulator = wsp.Simulator(
        until=60,
        timescale=1,
        visual=True,
        terrain_size=(650, 650),
        title="MACAW Grid Topology Demo"
    )

    topology = GridTopology()
    topology.set_nodes()
    topology.run()

    simulator.run()
