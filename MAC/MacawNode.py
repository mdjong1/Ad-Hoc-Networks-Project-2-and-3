import wsnsimpy.wsnsimpy_tk as wsp
import random

SENDING_RADIUS_TIME = 1  # second(s)
TX_CIRCLE_DELTA = 50  # how close are subsequent TX circles to one another

BASE_BACKOFF_TIME = 1  # second(s)
MAX_BACKOFF_TIME = 60  # seconds


def delay():
    return random.uniform(1, 2)


class MacawNode(wsp.Node):
    def __init__(self, sim, id, pos):
        super().__init__(sim, id, pos)
        self._data_length = 0
        self._rts_received = False
        self._in_data_transition = False
        self._rrts_target = None
        self._backoff_time = BASE_BACKOFF_TIME

    def backoff(self):
        if self._backoff_time < MAX_BACKOFF_TIME:
            yield self.timeout(self._backoff_time)
            self._backoff_time *= 2

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
        self.log(f"Send RTS to {target}")
        self.send(wsp.BROADCAST_ADDR, msg='RTS', target=target)

    def send_cts(self, target):
        self.log(f"Send CTS to {target}")
        self.send(wsp.BROADCAST_ADDR, msg='CTS', target=target)

    def send_ds(self, target, length):
        self.log(f"Send DS to {target}")
        self.send(wsp.BROADCAST_ADDR, msg='DS', target=target, length=length)

    def send_data(self, target, seq):
        self.log(f"Send DATA to {target}")
        self.send(wsp.BROADCAST_ADDR, msg='DATA', target=target, seq=seq)

    def send_ack(self, target):
        self.log(f"Send ACK to {target}")
        self.send(wsp.BROADCAST_ADDR, msg='ACK', target=target)

    def send_rrts(self):
        if self._rrts_target is not None:
            self.log(f"Send RRTS to {self._rrts_target}")
            self.send(wsp.BROADCAST_ADDR, msg='RRTS', target=self._rrts_target)
            self._rrts_target = None

    def start_send_data(self, target):
        # self.scene.clearlinks()
        seq = 1

        data_length = random.randint(5, 10)

        self.send_ds(target=target, length=data_length)

        for _ in range(data_length):
            yield self.timeout(1)
            self.send_data(target=target, seq=seq)
            seq += 1

    def on_receive(self, sender, msg, **kwargs):
        target = kwargs['target']

        # Detecting collisions!
        if self._in_data_transition:
            if msg != "DATA" and msg != "ACK":
                self.log(f"Collision!!!!!!")
            elif target != self.id:
                self.log(f"Collision!!!!!!")

        if msg == 'RRTS' and self.id == target:
            yield self.timeout(delay())
            self.send_rts(target=sender)

        elif msg == 'RTS':
            # self.scene.addlink(sender, self.id, "parent")

            if self.id == target and not self._rts_received:
                # Cannot send any other RTS if already send one
                self._rts_received = True
                self.log(f"Received RTS from {sender}")

                yield self.timeout(delay())
                # self.scene.clearlinks()

                yield self.timeout(delay())

                self.send_cts(target=sender)

            elif self.id == target and self._rts_received and not self._rrts_target:
                self.log(f"Got RTS while locked")
                self._rrts_target = sender

        elif msg == 'CTS':
            if self.id == target:
                self._in_data_transition = True

                self.log(f"Received CTS from {sender}")
                yield self.timeout(delay())
                self.log("Start sending data")
                self.start_process(self.start_send_data(target=sender))

        elif msg == 'DS':
            if self.id == target:
                self._in_data_transition = True
                self._rts_received = False
                length = kwargs['length']
                self.log(f"Got DS from {sender} with length {length}")
                self._data_length = length

        elif msg == 'DATA':
            if self.id == target:
                seq = kwargs['seq']
                self.log(f"Got DATA from {sender} with seq {seq}")

                if seq == self._data_length:
                    self._in_data_transition = False
                    self.log(f"Received all packets! {seq} of {self._data_length}")

                    yield self.timeout(delay())
                    self.send_ack(target=sender)
                    self.send_rrts()

        elif msg == 'ACK':
            if self.id == target:
                self._in_data_transition = False
                self.log(f"Received ACK from {sender}")

            elif self._rts_received and self._rrts_target:
                yield self.timeout(delay() * 2)
                self._rts_received = False
