"""
REQUIREMENTS:
This group project requires you to implement one MAC protocol and show a simulation of it in action.
The simulator should show the various nodes, and decide which nodes will send out packets at a given time.
The implemented MAC protocol should handle the wireless communication between the various nodes.
The number of nodes and traffic load should be configurable in the simulator to show how well the protocol performs
under varying loads. Report your observations on different aspects such as throughput, delay, losses, etc.
"""


# place nodes over 100x100 grids
for x in range(10):
    for y in range(10):
        px = 50 + x * 60 + random.uniform(-20, 20)
        py = 50 + y * 60 + random.uniform(-20, 20)
        node = simulator.add_node(MacawNode, (px, py))
        node.tx_range = 300
        node.logging = True

# start the simulation
simulator.run()
