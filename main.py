import random
import wsnsimpy.wsnsimpy_tk as wsp

SOURCE = 12  # random.randint(0, 10)
DEST = 36  # random.randint(90, 99)


def delay():
    return random.uniform(.2, .8)


class MacawNode(wsp.Node):
    def __init__(self, sim, id, pos):
        super().__init__(sim, id, pos)
        self._data_length = 0
        self._locked = False
        self._rrts_target = None

    def run(self):
        if self.id is SOURCE:
            self.scene.nodecolor(self.id, 0, 0, 1)
            self.scene.nodewidth(self.id, 2)
            yield self.timeout(1)
            self.log(f"Send RTS to {DEST}")
            self.send_rts(target=DEST)

        elif self.id is DEST:
            self.scene.nodecolor(self.id, 1, 0, 0)
            self.scene.nodewidth(self.id, 2)

        else:
            self.scene.nodecolor(self.id, .7, .7, .7)

    def send_rts(self, target):
        self.send(wsp.BROADCAST_ADDR, msg='RTS', target=target)

    def send_cts(self, target):
        self.send(wsp.BROADCAST_ADDR, msg='CTS', target=target)

    def send_ds(self, target, length):
        self.send(wsp.BROADCAST_ADDR, msg='DS', target=target, length=length)

    def send_data(self, target, seq):
        self.send(wsp.BROADCAST_ADDR, msg='DATA', target=target, seq=seq)

    def send_ack(self, target):
        self.send(wsp.BROADCAST_ADDR, msg='ACK', target=target)

    def send_rrts(self):
        self.send(wsp.BROADCAST_ADDR, msg='RRTS', target=self._rrts_target)
        self._rrts_target = None

    def start_send_data(self):
        self.scene.clearlinks()
        seq = 1

        data_length = random.randint(5, 10)

        self.log(f"Send DS to {DEST} with length {data_length}")
        self.send_ds(target=DEST, length=data_length)

        for _ in range(data_length):
            yield self.timeout(1)
            self.log(f"Send DATA to {DEST} with seq {seq}")
            self.send_data(target=DEST, seq=seq)
            seq += 1

    def on_receive(self, sender, msg, **kwargs):
        target = kwargs['target']
        if msg == 'RRTS':
            yield self.timeout(1)
            self.log(f"Send RTS to {sender}")
            self.send_rts(target=sender)

        elif msg == 'RTS':
            self.scene.addlink(sender, self.id, "parent")

            if self.id is target and not self._locked:
                self.log(f"Received RTS from {sender}")

                yield self.timeout(5)
                self.scene.clearlinks()

                yield self.timeout(2)
                self.log(f"Send CTS to {sender}")
                self.send_cts(target=sender)

            elif self.id is target and self._locked and not self._rrts_target:
                self._rrts_target = sender

        elif msg == 'CTS':
            if self.id is target:
                self.log(f"Received CTS from {sender}")
                yield self.timeout(5)
                self.log("Start sending data")
                self.start_process(self.start_send_data())

            else:
                self._locked = True

        elif msg == 'DS':
            if self.id is target:
                length = kwargs['length']
                self.log(f"Got DS from {sender} with length {length}")
                self._data_length = length

        elif msg == 'DATA':
            if self.id is target:
                seq = kwargs['seq']
                self.log(f"Got DATA from {sender} with seq {seq}")

                if seq == self._data_length:
                    self.log(f"Received all packets! {seq} of {self._data_length}")
                    yield self.timeout(2)
                    self.log(f"Send ACK to {sender}")
                    self.send_ack(target=sender)

        elif msg == 'ACK':
            if self.id is target:
                self.log(f"Received ACK from {sender}")

            elif self._locked and self._rrts_target:
                yield self.timeout(delay())
                self._locked = False
                self.send_rrts()


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
