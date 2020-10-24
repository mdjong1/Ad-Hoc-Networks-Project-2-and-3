import random
import wsnsimpy.wsnsimpy_tk as wsp

SOURCE = 12  # random.randint(0, 10)
DEST = 36  # random.randint(90, 99)


def delay():
    return random.uniform(.2, .8)


class MacawNode(wsp.Node):
    def __init__(self, sim, id, pos):
        super().__init__(sim, id, pos)
        self.source = None
        self._data_length = 0

    def run(self):
        if self.id is SOURCE:
            self.scene.nodecolor(self.id, 0, 0, 1)
            self.scene.nodewidth(self.id, 2)
            yield self.timeout(1)
            self.log(f"Send RTS to {DEST}")
            self.send_rts(src=self.id, target=DEST)

        elif self.id is DEST:
            self.scene.nodecolor(self.id, 1, 0, 0)
            self.scene.nodewidth(self.id, 2)

        else:
            self.scene.nodecolor(self.id, .7, .7, .7)

    def send_rts(self, src, target):
        self.send(wsp.BROADCAST_ADDR, msg='RTS', src=src, target=target)

    def send_cts(self, src, target):
        self.send(wsp.BROADCAST_ADDR, msg='CTS', src=src, target=target)

    def send_ds(self, src, target, length):
        self.send(wsp.BROADCAST_ADDR, msg='DS', src=src, target=target, length=length)

    def send_data(self, src, target, seq):
        self.send(wsp.BROADCAST_ADDR, msg='DATA', src=src, target=target, seq=seq)

    def send_ack(self, src, target):
        self.send(wsp.BROADCAST_ADDR, msg='ACK', src=src, target=target)

    def start_send_data(self):
        self.scene.clearlinks()
        seq = 1

        data_length = random.randint(5, 10)

        self.log(f"Send DS to {DEST} with length {data_length}")
        self.send_ds(src=self.id, target=DEST, length=data_length)

        for _ in range(data_length):
            yield self.timeout(1)
            self.log(f"Send DATA to {DEST} with seq {seq}")
            self.send_data(src=self.id, target=DEST, seq=seq)
            seq += 1

    def on_receive(self, sender, msg, src, **kwargs):
        target = kwargs['target']
        if msg == 'RTS':
            self.scene.addlink(sender, self.id, "parent")

            if self.id is target:
                self.source = sender
                self.log(f"Received RTS from {src}")
                yield self.timeout(5)
                self.scene.clearlinks()
                yield self.timeout(2)
                self.log(f"Send CTS to {src}")
                self.send_cts(src=self.id, target=self.source)

        elif msg == 'CTS':
            if self.id is target:
                self.log(f"Received CTS from {src}")
                yield self.timeout(5)
                self.log("Start sending data")
                self.start_process(self.start_send_data())

        elif msg == 'DS':
            if self.id is target:
                length = kwargs['length']
                self.log(f"Got DS from {src} with length {length}")
                self._data_length = length

        elif msg == 'DATA':
            if self.id is target:
                seq = kwargs['seq']
                self.log(f"Got DATA from {src} with seq {seq}")

                if seq == self._data_length:
                    self.log(f"Received all packets! {seq} of {self._data_length}")
                    yield self.timeout(2)
                    self.log(f"Send ACK to {src}")
                    self.send_ack(src=self.id, target=self.source)

        elif msg == 'ACK':
            if self.id is target:
                self.log(f"Received ACK from {src}")


simulator = wsp.Simulator(
    until=60,
    timescale=1,
    visual=True,
    terrain_size=(650, 650),
    title="MACAW Demo"
)

# define a line style for parent links
simulator.scene.linestyle("parent", color=(0, .7, 0), arrow="head", width=2)

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
