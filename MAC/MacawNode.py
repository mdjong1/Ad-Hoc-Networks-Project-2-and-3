import wsnsimpy.wsnsimpy_tk as wsp
import random
from config import *

IDLE_STATE = 0
SENDING_STATE = 1
RECEIVING_STATE = 2
BACKOFF_STATE = 3

# Wait one slot to give someone else the opportunity to receive a CTS
WAIT_STATE = 4

RTS_RECEIVED_STATE = 5


def delay():
    return random.uniform(1, 2)


class DataPacket():
    def __init__(self, length, target_id, time_offset=0):
        self.length = length
        self.target_id = target_id
        self.time_offset = time_offset


class MacawNode(wsp.LayeredNode):
    def __init__(self, sim, id, pos):
        super().__init__(sim, id, pos)
        self._state = IDLE_STATE
        self._data_queue = []  # Queue of data packets
        self._backoff_time = MIN_BACKOFF_TIME
        self._print_info = True

        # if this value exceeds CTS_TIMEOUT a cts is not received in time
        self._cts_timeout_counter = 0

    def run(self):
        while True:
            if(len(self._data_queue) > 0 and self._state == IDLE_STATE):
                self.start_process(self._start_transmission())

            if(self._print_info):
                info = "Node: " + str(self.id) + "\n" \
                    + "BO: " + str(self._backoff_time) + "\n" \
                    + "Queue: " + str(len(self._data_queue))
                self.scene.nodelabel(self.id, label=info)
            # allow others to execute
            yield self.timeout(0.1)

    # add data to the queue, data is beeing send when ready
    def add_data(self, length, target, time_offset=0):
        self._data_queue.append(DataPacket(length, target.id, time_offset))

    def _get_backoff_time(self):
        self.log(f"Backing off")
        return random.uniform(1, self._backoff_time)

    # use MILD algorithm to increase backoftime F_inc(x) = MAX[1.5x, BO_max]
    def _inc_backoff(self):
        self._backoff_time = round(self._backoff_time * 1.5)
        if(self._backoff_time > MAX_BACKOFF_TIME):
            self._backoff_time = MAX_BACKOFF_TIME

    # use MILD algorithm to decrease backoftime F_inc(x) = MAX[x-1, BO_max]
    def _dec_backoff(self):
        self._backoff_time -= 1
        if(self._backoff_time < MIN_BACKOFF_TIME):
            self._backoff_time = MIN_BACKOFF_TIME

    def _start_transmission(self):
        if(len(self._data_queue) > 0):
            packet = self._data_queue[0]
            current_slot = self.now
            # Check if it is time for the packet to be send.
            if(packet.time_offset <= current_slot):
                self._state = WAIT_STATE
                self._send_rts(packet.target_id, packet.length)

                # wait for a CTS packet to arrive.
                yield self.timeout(SLOT_TIME * 3)

                # the state is still WAIT_FOR_CTS_STATE a CTS is not arrived
                if(self._state == WAIT_STATE):
                    yield self.timeout(self._get_backoff_time())
                    self._inc_backoff()
                    self._state = IDLE_STATE
                    # Taken from the library but adjusted to transmission radius will remain active longer

    def send(self, dest, *args, **kwargs):
        circles = []
        msg = kwargs['msg']

        for circle_diam in range(0, self.tx_range + TX_CIRCLE_DELTA, TX_CIRCLE_DELTA):
            circle = self.scene.circle(
                self.pos[0], self.pos[1],
                circle_diam,
                line="wsnsimpy:tx")
            circles.append(circle)

        super().send(dest, *args, **kwargs)

        # time the packet need to send the data
        if(msg == "DATA"):
            radius_time = kwargs['data_length'] * BYTE_TRANSMISSION_TIME
        else:
            radius_time = DATA_LENGTH[msg] * BYTE_TRANSMISSION_TIME
        self.delayed_exec(radius_time, self._clear_circles, circles)

    def _clear_circles(self, circles):
        for circle in circles:
            self.scene.delshape(circle)

    def _send_rts(self, target_id, data_length):
        self.log(f"Send RTS to {target_id}")
        self.send(wsp.BROADCAST_ADDR, msg='RTS',
                  target_id=target_id, data_length=data_length)

    def _send_cts(self, target_id, data_length):
        self.log(f"Send CTS to {target_id}")
        self.send(wsp.BROADCAST_ADDR, msg='CTS',
                  target_id=target_id, data_length=data_length)

    def _send_ds(self, target, length):
        self.log(f"Send DS to {target}")
        self.send(wsp.BROADCAST_ADDR, msg='DS',
                  target=target, length=length)

    def _send_data(self):
        if(len(self._data_queue) > 0):
            packet = self._data_queue[0]
            self.log(f"Send DATA to {packet.target_id}")
            self.send(wsp.BROADCAST_ADDR, msg='DATA',
                      target_id=packet.target_id, data_length=packet.length)

    def _send_ack(self, target_id):
        self.log(f"Send ACK to {target_id}")
        self.send(wsp.BROADCAST_ADDR, msg='ACK', target_id=target_id)

    # def _send_rrts(self):
    #    if self._rrts_target is not None:
    #        self.log(f"Send RRTS to {self._rrts_target}")
    #        self.send(wsp.BROADCAST_ADDR, msg='RRTS', target=self._rrts_target)
    #        self._rrts_target = None

    def on_receive(self, sender_id, msg, **kwargs):
        target_id = kwargs['target_id']
        backoff = -1
        data_length = -1
        if('data_length' in kwargs):
            data_length = kwargs['data_length']
        if('backoff' in kwargs):
            backoff = kwargs['backoff']
        # # Detecting collisions!
        # if self._in_data_transition:
        #     if msg != "DATA" and msg != "ACK":
        #         self.log(f"Collision!!!!!!")
        #     elif target != self.id:
        #         self.log(f"Collision!!!!!!")

        # if msg == 'RRTS' and self.id == target:
        #     yield self.timeout(delay())
        #     self.send_rts(target=sender)

        if msg == 'RTS':
            # self.scene.addlink(sender, self.id, "parent")

            # Simulate the time a RTS packets takes to receive the node
            yield self.timeout(BYTE_TRANSMISSION_TIME * DATA_LENGTH["RTS"])

            if self.id == target_id and self._state == IDLE_STATE:

                # Cannot send any other RTS if already send one
                self._state = RTS_RECEIVED_STATE
                self.log(f"Received RTS from {sender_id}")
                # self.scene.clearlinks()

                self._send_cts(sender_id, data_length)

                yield self.timeout(SLOT_TIME * 2)

                # If the state is not update to RECEIVING_STATE something went
                # wrong and we should reset to IDLE state
                if(self._state == RTS_RECEIVED_STATE):
                    self.log(
                        f"No data received from sender, returning to idle state")
                    self._state = IDLE_STATE

            elif self.id == target_id and self._state == RTS_RECEIVED_STATE:
                self.log(f"We already received a RTS from someone else")
                # self._rrts_target = sender
            # RTS is not meant for us we should wait and the the reiver time to send a CTS (1 time slot)
            elif self.id != target_id:
                self.log(f"\"Received a RTS from {sender_id}\"")
                self._state = WAIT_STATE
                yield self.timeout(SLOT_TIME * 2)
                self._state = IDLE_STATE

        elif msg == 'CTS':
            if self.id == target_id:
                # Simulate the time a CTS packets takes to receive the node
                yield self.timeout(BYTE_TRANSMISSION_TIME * DATA_LENGTH["RTS"])
                self._dec_backoff()
                self.log(f"Received CTS from {sender_id}")
                self._state = SENDING_STATE
                # We can send data now #lifegoals
                self._send_data()

            # Message is not meant for us we should wait until data transfer is finished
            else:
                self.log(f"\"Received CTS from {sender_id}\"")
                yield self.timeout(data_length * BYTE_TRANSMISSION_TIME)

                # elif msg == 'DS':
                #     if self.id == target:
                #         self._in_data_transition = True
                #         self._rts_received = False
                #         length = kwargs['length']
                #         self.log(f"Got DS from {sender} with length {length}")
                #         self._data_length = length

        elif msg == 'DATA':
            # we don't have carrier sensing, so we do not do anything
            # with a data packet that is not meant for us
            if self.id == target_id:

                # Simulate time it takes to transmite data
                self._state = RECEIVING_STATE
                yield self.timeout(BYTE_TRANSMISSION_TIME * data_length)
                self.log(
                    f"Got DATA from {sender_id} with data length {data_length}")

                self._send_ack(sender_id)
                self._state = IDLE_STATE

        elif msg == 'ACK':
            if self.id == target_id:
                # Simulate time it takes to transmite ACK message
                yield self.timeout(BYTE_TRANSMISSION_TIME * DATA_LENGTH["ACK"])
                # we can finally remove the data packet from the queue yeah
                self.log(f"Received ACK from {sender_id}")
                self._data_queue.pop(0)
                self._state = IDLE_STATE
                self._backoff_time = MIN_BACKOFF_TIME
