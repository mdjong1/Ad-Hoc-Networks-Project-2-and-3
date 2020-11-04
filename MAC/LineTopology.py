from MacawNode import MacawNode
import wsnsimpy.wsnsimpy_tk as wsp


class LineTopology:

    def __init__(self):
        self.nodes = []

    def set_nodes(self):
        for x in range(3):
            self.nodes.append(simulator.add_node(
                MacawNode, (225 + (100 * x), 200)))
            self.nodes[x].tx_range = 100

    def run(self):
        target = self.nodes[2]
        self.nodes[1].add_data(256, target)
        self.nodes[1].add_data(256, target)
        self.nodes[1].add_data(256, target)
        self.nodes[1].add_data(256, target)

        target = self.nodes[1]
        self.nodes[0].add_data(256, target, time_offset=1)


if __name__ == '__main__':
    simulator = wsp.Simulator(
        until=60,
        timescale=1,
        visual=True,
        terrain_size=(650, 650),
        title="MACAW Line Topology Demo"
    )

    topology = LineTopology()
    topology.set_nodes()
    topology.run()

    simulator.run()
