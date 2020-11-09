import Routing

if __name__ == '__main__':
    import random
    import wsnsimpy.wsnsimpy_tk as wsp
    from Routing.AODVNode import MyNode

    terrain_size = 600
    terrain_margin = 80
    playfield = terrain_size - 2 * terrain_margin

    # Initiate simulator
    Routing.simulator = wsp.Simulator(
        until=150,
        timescale=1,
        visual=True,
        terrain_size=(terrain_size, terrain_size),
        title="Dynamic AODV Demo"
    )

    # Define a line style for parent links
    Routing.simulator.scene.linestyle("parent", color=(0, .8, 0), arrow="tail", width=2)

    # Place nodes in grid with random offset
    node_distance = playfield / 6
    for x in range(7):
        for y in range(7):
            px = terrain_margin + x * node_distance + random.uniform(-20, 20)
            py = terrain_margin + y * node_distance + random.uniform(-20, 20)
            node = Routing.simulator.add_node(MyNode, (px, py))
            node.tx_range = 95
            node.logging = True

    source_node = Routing.simulator.nodes[1]
    # In order to allow a function to use timeouts (delays),
    # it has to be started as a 'process'
    source_node.start_process(source_node.start_send_to(len(Routing.simulator.nodes) - 1))
    source_node.print_table()

    # Start simulation
    Routing.simulator.run()
