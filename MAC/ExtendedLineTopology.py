from MacawNode import MacawNode
import wsnsimpy.wsnsimpy_tk as wsp


class ExtendedLineTopology:

    def __init__(self):
        self.nodes = []

    def set_nodes(self):
        for x in range(4):
            self.nodes.append(simulator.add_node(MacawNode, (175 + (100 * x), 200)))
            self.nodes[x].tx_range = 100

    def run(self):
        target = self.nodes[0].id
        self.nodes[1].send_rts(target)

        target = self.nodes[3].id
        self.nodes[2].send_rts(target)


if __name__ == '__main__':
    simulator = wsp.Simulator(
        until=60,
        timescale=1,
        visual=True,
        terrain_size=(650, 650),
        title="MACAW Extended Line Topology Demo"
    )

    lineTop = ExtendedLineTopology()
    lineTop.set_nodes()
    lineTop.run()

    simulator.run()
