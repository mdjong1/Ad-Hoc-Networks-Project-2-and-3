from Routing.textstyles import TStyle
import random
import Routing


demo_index = 0  # Used by the demo control function


def clear_board():
    """Reset all node styles to grey and width 1"""
    for node in Routing.simulator.nodes:
        Routing.simulator.scene.nodecolor(node.id, .7, .7, .7)
        Routing.simulator.scene.nodewidth(node.id, 1)


def demo_control_callback():
    """Function that defines the demo that we're showing"""
    global demo_index
    demo_index += 1
    n_nodes = len(Routing.simulator.nodes)

    print(f"\n{TStyle.RED}{TStyle.BOLD}Demo control callback {demo_index}{TStyle.ENDC}")

    # First do the same route again
    if demo_index == 1:
        # Reset styles
        clear_board()

        source_node = Routing.simulator.nodes[1]
        dest_id = n_nodes - 1
        source_node.print_table()

        print(f"{TStyle.UNDERLINE}Same source & destination{TStyle.ENDC}")
        source_node.start_process(source_node.start_send_to(dest_id))
    # Then, same route, but break a link
    elif demo_index == 2:
        clear_board()

        source_node = Routing.simulator.nodes[1]
        dest_id = n_nodes - 1
        # Remove a node in the path
        node = source_node
        # Follow the route for 3 links
        for i in range(4):
            node = Routing.simulator.nodes[node.table[dest_id]["next"]]
        node.move(5000, 5000)  # Move the node far away to "remove" it.
        print(f"{TStyle.UNDERLINE}Removing node {node.id}{TStyle.ENDC}")

        source_node.start_process(source_node.start_send_to(dest_id))
    # 3 data transfers between random nodes
    elif demo_index < 5:
        Routing.simulator.nodes[1].print_table()
        # Reset styles
        clear_board()

        # Fixme: make sure the nodes are not too close together and also not the removed node and also not itself!
        new_sender = Routing.simulator.nodes[random.randint(0, n_nodes - 1)]
        new_receiver = Routing.simulator.nodes[random.randint(0, n_nodes - 1)]
        new_sender.start_process(new_sender.start_send_to(new_receiver.id))
    # 3 simultaneous data transfers
    elif demo_index == 5:
        # Reset styles after previous example and turn off arrows and logging
        clear_board()
        for node in Routing.simulator.nodes:
            node.logging = False
            node.draw_arrows = False

        # Start 3 simultaneous processes
        print(f"{TStyle.UNDERLINE}Starting 3 processes{TStyle.ENDC}")
        for i in range(3):
            new_sender = Routing.simulator.nodes[random.randint(0, n_nodes - 1)]
            new_receiver = Routing.simulator.nodes[random.randint(0, n_nodes - 1)]
            new_sender.start_process(new_sender.start_send_to(new_receiver.id))
    elif demo_index < 8:
        pass  # wait for previous processes to finish
    else:
        clear_board()
        # Print a random node's table
        Routing.simulator.nodes[random.randint(0, n_nodes - 1)].print_table()
