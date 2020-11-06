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

    # Let's do 3 data transfers total
    if demo_index < 3:
        # Reset styles
        clear_board()

        new_sender = Routing.simulator.nodes[random.randint(0, n_nodes - 1)]
        new_receiver = Routing.simulator.nodes[random.randint(0, n_nodes - 1)]
        new_sender.start_process(new_sender.start_send_to(new_receiver.id))

    elif demo_index == 3:
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
    elif demo_index < 6:
        pass  # wait for previous processes to finish
    else:
        clear_board()
        # Print a random node's table
        Routing.simulator.nodes[random.randint(0, n_nodes - 1)].print_table()
