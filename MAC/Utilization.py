import time

from wsnsimpy.wsnsimpy_tk import Simulator


class Utilization:
    def __init__(self, simulator: Simulator, nodes: list):
        self._simulator = simulator
        self._nodes = nodes

        self._simulator.tkplot.canvas.create_text(100, 590, font="Times 12", text="Network Utilization:")
        self._text = self._simulator.tkplot.canvas.create_text(100, 615, font="Times 12", text="0 packets/second")

        self.start_utilization_update_loop()

    def update_utilization(self, utilization: int):
        plural = "" if utilization == 1 else "s"
        self._simulator.tkplot.canvas.itemconfigure(self._text, text=str(utilization) + " packet" + plural + "/second")

    def start_utilization_update_loop(self):
        while True:
            total_packets = 0

            for node in self._nodes:
                total_packets += node.packets_received
                node.packets_received = 0

            self.update_utilization(total_packets)

            time.sleep(1)
