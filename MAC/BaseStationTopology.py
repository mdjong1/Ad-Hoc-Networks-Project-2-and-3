from MacawNode import MacawNode
import wsnsimpy.wsnsimpy_tk as wsp

PACKET_SIZE = 256


class LineTopology:

    def __init__(self):
        self.nodes = []

    def set_nodes(self):
        for x in range(3):
            self.nodes.append(simulator.add_node(
                MacawNode, (225 + (100 * x), 200)))
            self.nodes[x].tx_range = 200

    def run(self):
        baseStation = self.nodes[1]
        for n in range(5):
            self.nodes[0].add_data(PACKET_SIZE, baseStation)

        self.nodes[2].add_data(PACKET_SIZE, baseStation, time_offset=1)


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
