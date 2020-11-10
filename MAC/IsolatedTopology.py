import random
import threading

from MacawNode import MacawNode
import wsnsimpy.wsnsimpy_tk as wsp

from Utilization import Utilization

PACKET_SIZE = 256
NUM_NODES_PER_CLUSTER = 3
CLUSTERS = [
    [50, 50, 150, 150],
    [450, 50, 600, 150],
    [50, 350, 150, 450],
    [450, 450, 600, 600]
]


class IsolatedTopology:

    def __init__(self):
        self.nodes = []

    def set_nodes(self):
        for cluster in CLUSTERS:
            for _ in range(NUM_NODES_PER_CLUSTER):
                self.nodes.append(
                    simulator.add_node(
                        MacawNode,
                        (
                            cluster[0] + random.randint(0, cluster[2] - cluster[0]),
                            cluster[1] + random.randint(0, cluster[3] - cluster[1])
                        )
                    )
                )

        for node in self.nodes:
            node.tx_range = 150

    def run(self):
        for cluster in range(len(CLUSTERS)):
            min_val = cluster * NUM_NODES_PER_CLUSTER
            max_val = cluster * NUM_NODES_PER_CLUSTER + NUM_NODES_PER_CLUSTER - 1

            sender = self.nodes[random.randint(min_val, max_val)]
            # Ensure receiver != sender
            receiver = self.nodes[random.choice([i for i in range(min_val, max_val) if i != sender.id])]

            sender.add_data(PACKET_SIZE, receiver, time_offset=random.randint(0, 4))


if __name__ == '__main__':
    simulator = wsp.Simulator(
        until=60,
        timescale=1,
        visual=True,
        terrain_size=(650, 650),
        title="MACAW Isolated Topology Demo"
    )

    topology = IsolatedTopology()
    topology.set_nodes()
    topology.run()

    threading.Thread(target=Utilization, args=(simulator, topology.nodes,)).start()

    simulator.run()
