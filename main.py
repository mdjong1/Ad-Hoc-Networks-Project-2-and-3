import random
import wsnsimpy.wsnsimpy_tk as wsp

SOURCE = 1
DEST = 99


def delay():
    return random.uniform(.2, .8)


class MyNode(wsp.Node):
    tx_range = 100

    def __init__(self, sim, id, pos):
        super().__init__(sim, id, pos)
        self.prev = None
        self.next = None

    def init(self):
        super().init()

    def run(self):
        if self.id is SOURCE:
            self.scene.nodecolor(self.id, 0, 0, 1)
            self.scene.nodewidth(self.id, 2)
            yield self.timeout(1)
            self.log(f"Send RTS to {DEST}")
            self.send_rts(self.id)

        elif self.id is DEST:
            self.scene.nodecolor(self.id, 1, 0, 0)
            self.scene.nodewidth(self.id, 2)

        else:
            self.scene.nodecolor(self.id, .7, .7, .7)

    def send_rts(self, src):
        self.send(wsp.BROADCAST_ADDR, msg='RTS', src=src)

    def send_cts(self, src):
        if self.id is not DEST:
            self.scene.nodecolor(self.id, 0, .7, 0)
            self.scene.nodewidth(self.id, 2)
        self.send(self.prev, msg='CTS', src=src)

    def start_send_data(self):
        self.scene.clearlinks()
        seq = 0
        while True:
            yield self.timeout(1)
            self.log(f"Send data to {DEST} with seq {seq}")
            self.send_data(self.id, seq)
            seq += 1

    def send_data(self, src, seq):
        self.log(f"Forward data with seq {seq} via {self.next}")
        self.send(self.next, msg='DATA', src=src, seq=seq)

    def on_receive(self, sender, msg, src, **kwargs):
        if msg == 'RTS':
            if self.prev is not None:
                return

            self.prev = sender
            self.scene.addlink(sender, self.id, "parent")

            if self.id is DEST:
                self.log(f"Received RTS from {src}")
                yield self.timeout(5)
                self.log(f"Send CTS to {src}")
                self.send_cts(self.id)

            else:
                yield self.timeout(delay())
                self.send_rts(src)

        elif msg == 'CTS':
            self.next = sender

            if self.id is SOURCE:
                self.log(f"Received CTS from {src}")
                yield self.timeout(5)
                self.log("Start sending data")
                self.start_process(self.start_send_data())

            else:
                yield self.timeout(.2)
                self.send_cts(src)

        elif msg == 'DATA':
            if self.id is not DEST:
                yield self.timeout(.2)
                self.send_data(src, **kwargs)

            else:
                seq = kwargs['seq']
                self.log(f"Got data from {src} with seq {seq}")


sim = wsp.Simulator(
    until=100,
    timescale=1,
    visual=True,
    terrain_size=(700, 700),
    title="MACAW Demo")

# define a line style for parent links
sim.scene.linestyle("parent", color=(0, .8, 0), arrow="tail", width=2)

# place nodes over 100x100 grids
for x in range(10):
    for y in range(10):
        px = 50 + x * 60 + random.uniform(-20, 20)
        py = 50 + y * 60 + random.uniform(-20, 20)
        node = sim.add_node(MyNode, (px, py))
        node.tx_range = 75
        node.logging = True

# start the simulation
sim.run()
