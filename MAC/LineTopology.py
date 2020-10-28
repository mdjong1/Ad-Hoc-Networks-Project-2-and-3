from Simulator import simulator
from MacawNode import MacawNode


class LineTopology:

    def __init__(self):
        self.nodes = []
        pass

    def set_nodes(self):
        for x in range(3):
            self.nodes.append(simulator.add_node(
                MacawNode, (50 + (100 * x), 50)))
            self.nodes[x].tx_range = 100

    def run(self):
        target = self.nodes[1].id
        self.nodes[0].send_rts(target)
        self.nodes[2].send_rts(target)


if __name__ == '__main__':
    lineTop = LineTopology()
    lineTop.set_nodes()
    lineTop.run()
    simulator.run()
