import wsnsimpy.wsnsimpy_tk as wsp
import random

SOURCE = 12
DEST = 36
COLLISION_SOURCE = 89
COLLISION_DEST = 57
NON_COLLISION_SOURCE = 90
NON_COLLISION_DEST = 72

SENDING_RADIUS_TIME = 1  # second
TX_CIRCLE_DELTA = 50  # how close are subsequent TX circles to one another


def delay():
    return random.uniform(1, 2)


class MacawNode(wsp.Node):
    def __init__(self, sim, id, pos):
        super().__init__(sim, id, pos)
        self._data_length = 0
        self._rts_received = False
        self._in_data_transition = False
        self._rrts_target = None

    def run(self):
        pass
        # if self.id is SOURCE:
        #  self.scene.nodecolor(self.id, 0, 0, 1)
        #  self.scene.nodewidth(self.id, 2)
        #  yield self.timeout(delay())
        #  self.log(f"Send RTS to {DEST}")
        #  self.send_rts(target=DEST)

        # elif self.id is DEST:
        #  self.scene.nodecolor(self.id, 1, 0, 0)
        #  self.scene.nodewidth(self.id, 2)

        # elif self.id == COLLISION_SOURCE:
        #  self.scene.nodecolor(self.id, 0, .8, 1)
        #  self.scene.nodewidth(self.id, 2)
        #  yield self.timeout(delay() * 5)
        #  self.log(f"Send RTS to {COLLISION_DEST}")
        #  self.send_rts(target=COLLISION_DEST)

        # elif self.id == COLLISION_DEST:
        #  self.scene.nodecolor(self.id, 1, .8, 0)
        #  self.scene.nodewidth(self.id, 2)

        # elif self.id == NON_COLLISION_SOURCE:
        #  self.scene.nodecolor(self.id, 0, .5, .7)
        #  self.scene.nodewidth(self.id, 2)
        #  yield self.timeout(delay())
        #  self.log(f"Send RTS to {NON_COLLISION_DEST}")
        #  self.send_rts(target=NON_COLLISION_DEST)

        # elif self.id == NON_COLLISION_DEST:
        #  self.scene.nodecolor(self.id, .9, .7, .2)
        #  self.scene.nodewidth(self.id, 2)

        # else:
        #  self.scene.nodecolor(self.id, .5, .5, .5)

        # Taken from the library but adjusted to transmission radius will remain active longer
    def send(self, dest, *args, **kwargs):
        circles = []

        for circle_diam in range(0, self.tx_range + TX_CIRCLE_DELTA, TX_CIRCLE_DELTA):
            circle = self.scene.circle(
                self.pos[0], self.pos[1],
                circle_diam,
                line="wsnsimpy:tx")
            circles.append(circle)

        super().send(dest, *args, **kwargs)

        self.delayed_exec(SENDING_RADIUS_TIME, self.clear_circles, circles)

    def clear_circles(self, circles):
        for circle in circles:
            self.scene.delshape(circle)

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
        if(self._rrts_target is not None):
            self.send(wsp.BROADCAST_ADDR, msg='RRTS', target=self._rrts_target)
            self._rrts_target = None

    def start_send_data(self, target):
        # self.scene.clearlinks()
        seq = 1

        data_length = random.randint(5, 10)

        self.log(f"Send DS to {target} with length {data_length}")
        self.send_ds(target=target, length=data_length)

        for _ in range(data_length):
            yield self.timeout(1)
            self.log(f"Send DATA to {target} with seq {seq}")
            self.send_data(target=target, seq=seq)
            seq += 1

    def on_receive(self, sender, msg, **kwargs):
        target = kwargs['target']

        # Detecting collisions!
        if self._in_data_transition:
            if(msg != "DATA" and msg != "ACK"):
                self.log(f"Collision!!!!!!")
            elif(target != self.id):
                self.log(f"Collision!!!!!!")

        if msg == 'RRTS' and self.id is target:
            yield self.timeout(delay())
            self.log(f"Send RTS to {sender}")
            self.send_rts(target=sender)

        elif msg == 'RTS':
            # self.scene.addlink(sender, self.id, "parent")

            if self.id is target and not self._rts_received:
                # Cannot send any other RTS if already send one
                self._rts_received = True
                self.log(f"Received RTS from {sender}")

                yield self.timeout(delay())
                # self.scene.clearlinks()

                yield self.timeout(delay())
                self.log(f"Send CTS to {sender}")
                self.send_cts(target=sender)

            elif self.id is target and self._rts_received and not self._rrts_target:
                self.log(f"Got RTS while locked")
                self._rrts_target = sender

        elif msg == 'CTS':
            if self.id is target:
                self._in_data_transition = True

                self.log(f"Received CTS from {sender}")
                yield self.timeout(delay())
                self.log("Start sending data")
                self.start_process(self.start_send_data(target=sender))

        elif msg == 'DS':
            if self.id is target:
                self._in_data_transition = True
                self._rts_received = False
                length = kwargs['length']
                self.log(f"Got DS from {sender} with length {length}")
                self._data_length = length

        elif msg == 'DATA':
            if self.id is target:
                seq = kwargs['seq']
                self.log(f"Got DATA from {sender} with seq {seq}")

                if seq == self._data_length:
                    self._in_data_transition = False
                    self.log(
                        f"Received all packets! {seq} of {self._data_length}")
                    yield self.timeout(delay())
                    self.log(f"Send ACK to {sender}")
                    self.send_ack(target=sender)
                    self.send_rrts()

        elif msg == 'ACK':
            if self.id is target:
                self._in_data_transition = False
                self.log(f"Received ACK from {sender}")

            elif self._rts_received and self._rrts_target:
                yield self.timeout(delay() * 2)
                self.log(f"Send RRTS to {self._rrts_target}")
                self._rts_received = False
