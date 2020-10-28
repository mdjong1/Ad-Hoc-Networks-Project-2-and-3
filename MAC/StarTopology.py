from math import sin, cos, pi

from MacawNode import MacawNode
import wsnsimpy.wsnsimpy_tk as wsp


NUM_STAR_TIPS = 5
CIRCLE_RADIUS = 200
ORIGIN_X = 325
ORIGIN_Y = 325


class StarTopology:

    def __init__(self):
        self.nodes = []

    def set_nodes(self):
        node = simulator.add_node(MacawNode, (ORIGIN_X, ORIGIN_Y))
        node.tx_range = CIRCLE_RADIUS
        self.nodes.append(node)

        for angle in range(0, 360, int(360 / NUM_STAR_TIPS)):
            angle = angle * pi/180  # To radians

            x = ORIGIN_X + int(CIRCLE_RADIUS * cos(angle))
            y = ORIGIN_Y + int(CIRCLE_RADIUS * sin(angle))

            node = simulator.add_node(MacawNode, (x, y))
            node.tx_range = CIRCLE_RADIUS
            self.nodes.append(node)

    def run(self):
        target = self.nodes[0].id
        self.nodes[1].send_rts(target)
        self.nodes[4].send_rts(target)
        # self.nodes[3].send_rts(target)


if __name__ == '__main__':
    simulator = wsp.Simulator(
        until=60,
        timescale=1,
        visual=True,
        terrain_size=(650, 650),
        title="MACAW Star Topology Demo"
    )

    star_topology = StarTopology()
    star_topology.set_nodes()
    star_topology.run()

    simulator.run()
