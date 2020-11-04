from MacawNode import MacawNode
import wsnsimpy.wsnsimpy_tk as wsp
from config import SLOT_TIME


class ExtendedLineTopology:

    def __init__(self):
        self.nodes = []

    def set_nodes(self):
        for x in range(4):
            self.nodes.append(simulator.add_node(MacawNode, (175 + (100 * x), 200)))
            self.nodes[x].tx_range = 100

    def run(self):
        target = self.nodes[0]
        self.nodes[1].add_data(100, target)


if __name__ == '__main__':
    simulator = wsp.Simulator(
        until=60,
        timescale=SLOT_TIME,
        visual=True,
        terrain_size=(650, 650),
        title="MACAW Extended Line Topology Demo"
    )

    topology = ExtendedLineTopology()
    topology.set_nodes()
    topology.run()

    simulator.run()
