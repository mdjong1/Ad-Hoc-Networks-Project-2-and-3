import wsnsimpy.wsnsimpy_tk as wsp
import random
from config import *

IDLE_STATE = 0
SENDING_STATE = 1
RECEIVING_STATE = 2
BACKOFF_STATE = 3

# Wait one slot to give someone else the opportunity to receive a CTS
WAIT_STATE = 4

# Wait for a neighboard to finish its data transmission to anohter
# neighboard. Enters this state after receiveing a CTS for someone else
WAIT_FOR_DATA = 5
RTS_RECEIVED_STATE = 6


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

        # Store node ids that are bussy transmitting data. It is useless to send
        # a RTS to that node. Set when a DS is received
        self._nodes_bussy = set()

        # Add node id if rts is received but we cannot send a CTS back due to
        # data transmission. When a ACK is receied RRTS will be send to all
        # these nodes
        self._received_rts = set()

        self.scene.linestyle('wsnsimpy:data', color=(1, 0, 0), dash=(3, 3))

        # if this value exceeds CTS_TIMEOUT a cts is not received in time
        self._cts_timeout_counter = 0

    def run(self):
        while True:
            if len(self._data_queue) > 0 and self._state == IDLE_STATE:
                self.start_process(self._start_transmission())

            if self._print_info:
                info = "Node: " + str(self.id) + "\n" \
                    + "BO: " + str(self._backoff_time) + "\n" \
                    + "Queue: " + str(len(self._data_queue))
                self.scene.nodelabel(self.id, label=info)

            # allow others to execute, because python somehow cannot do things i
            # in parallel -.-'
            yield self.timeout(0.5)

    # add data to the queue, data is beeing send when ready
    def add_data(self, length, target, time_offset=0):
        self._data_queue.append(DataPacket(length, target.id, time_offset))

    def _get_backoff_time(self):
        backoff_time = round(random.uniform(1, self._backoff_time))
        self.log(f"Backing off for {backoff_time} slots")
        return backoff_time * SLOT_TIME
    # use MILD algorithm to increase backoftime F_inc(x) = MAX[1.5x, BO_max]

    def _inc_backoff(self):
        self._backoff_time = round(self._backoff_time * 1.5)
        if self._backoff_time > MAX_BACKOFF_TIME:
            self._backoff_time = MAX_BACKOFF_TIME

    # use MILD algorithm to decrease backoftime F_inc(x) = MAX[x-1, BO_max]
    def _dec_backoff(self):
        self._backoff_time -= 1
        if self._backoff_time < MIN_BACKOFF_TIME:
            self._backoff_time = MIN_BACKOFF_TIME

    def _start_transmission(self):
        if len(self._data_queue) > 0:
            packet = self._data_queue[0]
            current_slot = self.now
            # Check if it is time for the packet to be send and that the node
            # to send it to is not bussy.
            if packet.time_offset <= current_slot \
                    and packet.target_id not in self._nodes_bussy:
                self._state = WAIT_STATE
                self._send_rts(packet.target_id, packet.length)

                # wait for a CTS packet to arrive.
                yield self.timeout(SLOT_TIME * 3)

                # the state is still WAIT_FOR_CTS_STATE a CTS is not arrived
                if self._state == WAIT_STATE:
                    self._state = BACKOFF_STATE
                    backoff_time = self._get_backoff_time()
                    yield self.timeout(backoff_time)
                    self._inc_backoff()

                    # if DS is received during backoff, we should not go into
                    # idle mode
                    if self._state == BACKOFF_STATE:
                        self._state = IDLE_STATE

    def send(self, dest, *args, **kwargs):
        circles = []
        msg = kwargs['msg']

        kwargs['backoff'] = self._backoff_time
        # time the packet need to send the data
        if msg == "DATA":
            radius_time = kwargs['data_length'] * BYTE_TRANSMISSION_TIME
            line_style = "wsnsimpy:data"

        else:
            radius_time = DATA_LENGTH[msg] * BYTE_TRANSMISSION_TIME
            line_style = "wsnsimpy:tx"

        for circle_diam in range(0, self.tx_range + TX_CIRCLE_DELTA, TX_CIRCLE_DELTA):
            circle = self.scene.circle(
                self.pos[0], self.pos[1], circle_diam, line=line_style)
            circles.append(circle)

        super().send(dest, *args, **kwargs)

        self.delayed_exec(radius_time, self._clear_circles, circles)

    def _clear_circles(self, circles):
        for circle in circles:
            self.scene.delshape(circle)

    def _send_rts(self, target_id, data_length):
        self.log(f"Send RTS to {target_id}")
        self.send(wsp.BROADCAST_ADDR, msg='RTS',
                  target_id=target_id, data_length=data_length)

    def _send_rrts(self, target_id):
        self.log(f"Send RRTS to {target_id}")
        self.send(wsp.BROADCAST_ADDR, msg='RRTS',
                  target_id=target_id)

    def _send_cts(self, target_id, data_length):
        self.log(f"Send CTS to {target_id}")
        self.send(wsp.BROADCAST_ADDR, msg='CTS',
                  target_id=target_id, data_length=data_length)

    def _send_ds(self):
        if len(self._data_queue) > 0:
            self._state = SENDING_STATE
            packet = self._data_queue[0]
            self.log(f"Send DS to {packet.target_id}")
            self.send(wsp.BROADCAST_ADDR, msg='DS',
                      target_id=packet.target_id, data_length=packet.length)

    def _send_data(self):
        if len(self._data_queue) > 0:
            self._state = SENDING_STATE
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
        data_length = -1

        if 'data_length' in kwargs:
            data_length = kwargs['data_length']

        if 'backoff' in kwargs:
            self._backoff_time = kwargs['backoff']

        # Detect collisions
        if self._state == RECEIVING_STATE and msg != "DATA":
            self.log(f"ERROR: Collision detected while receiving data")

        ################
        # Received RTS #
        ################
        if msg == 'RTS':
            # self.scene.addlink(sender, self.id, "parent")

            # Simulate the time a RTS packets takes to receive the node
            yield self.timeout(BYTE_TRANSMISSION_TIME * DATA_LENGTH["RTS"])

            if self.id == target_id:
                if self._state == IDLE_STATE:

                    # Cannot send any other RTS if already send one
                    self._state = RTS_RECEIVED_STATE
                    self.log(f"Received RTS from {sender_id}")
                    # self.scene.clearlinks()

                    self._send_cts(sender_id, data_length)

                    yield self.timeout(SLOT_TIME * 3)

                    # If the state is not update to RECEIVING_STATE something went
                    # wrong and we should reset to IDLE state
                    if self._state == RTS_RECEIVED_STATE:
                        self.log(
                            f"No data received from sender, returning to idle state")
                        self._state = IDLE_STATE

                elif self._state == RTS_RECEIVED_STATE:
                    self.log(f"We already received a RTS from someone else")

                elif self._state == WAIT_FOR_DATA:
                    # store sender_id to received_rts list to send a RRTS to alteron
                    self._received_rts.add(sender_id)

            # RTS is not meant for us we should wait and the the reiver time to send a CTS (1 time slot)
            elif self.id != target_id:
                self.log(f"\"Received a RTS from {sender_id}\"")
                # Allow others to receive the CTS of this RTC message
                if self._state == IDLE_STATE:
                    self._state = WAIT_STATE
                    yield self.timeout(SLOT_TIME * 3)
                    # make sure a CTS for someone else has not arrived in
                    # the meaintime
                    if(self._state == WAIT_STATE):
                        self._state = IDLE_STATE

        #################
        # Received RRTS #
        #################
        elif msg == "RRTS":
            if self._state == BACKOFF_STATE:
                if(self._data_queue[0].target_id == sender_id):
                    self.start_process(self._start_transmission())

        ################
        # Received CTS #
        ################
        elif msg == 'CTS':
            if self.id == target_id:
                # Simulate the time a CTS packets takes to receive the node
                yield self.timeout(BYTE_TRANSMISSION_TIME * DATA_LENGTH["RTS"])
                self._dec_backoff()
                self.log(f"Received CTS from {sender_id}")
                self._state = SENDING_STATE

                self._send_ds()
                # If we do not add a small delay here, the simulator sees a
                # collision between the DS and DATA packet somehow.
                yield self.timeout(0.1)
                # We can send data now #lifegoals
                self._send_data()

                # Wait for ACK
                yield self.timeout(data_length * BYTE_TRANSMISSION_TIME)
                yield self.timeout(DATA_LENGTH["ACK"] * BYTE_TRANSMISSION_TIME)
                yield self.timeout(SLOT_TIME)

                # If still in sending state, we did not receive a ACK and should try it again
                if self._state == SENDING_STATE:
                    self.log(f"No ACK received, trying again when possible")
                    self._state = IDLE_STATE

            # Message is not meant for us we should wait until data transfer is finished
            else:
                self.log(f"\"Received CTS from {sender_id}\"")
                # Avoid collision by waiting until data transmission is done
                self._state = WAIT_FOR_DATA
                yield self.timeout(DATA_LENGTH["DS"] * BYTE_TRANSMISSION_TIME)
                yield self.timeout(data_length * BYTE_TRANSMISSION_TIME)
                yield self.timeout(DATA_LENGTH["ACK"] * BYTE_TRANSMISSION_TIME)
                self._state = IDLE_STATE

        ###############
        # Received DS #
        ###############
        elif msg == 'DS':
            if self.id != target_id:
                # Simulate the time a DS packets takes to receive the node
                yield self.timeout(BYTE_TRANSMISSION_TIME * DATA_LENGTH["DS"])
                self.log(f"Received DS from {sender_id}")

                # No need to set the state to waiting because you can still send
                # RTSs to other nodes
                self._nodes_bussy.add(sender_id)
                yield self.timeout(DATA_LENGTH["DS"] * BYTE_TRANSMISSION_TIME)
                yield self.timeout(data_length * BYTE_TRANSMISSION_TIME)
                # yield self.timeout(DATA_LENGTH["ACK"] * BYTE_TRANSMISSION_TIME)
                self._nodes_bussy.remove(sender_id)

        #################
        # Received DATA #
        #################
        elif msg == 'DATA':
            # we don't have carrier sensing, so we do not do anything
            # with a data packet that is not meant for us
            if self.id == target_id:

                # Simulate time it takes to transmite data
                self._state = RECEIVING_STATE
                yield self.timeout(BYTE_TRANSMISSION_TIME * data_length)
                self.log(
                    f"Got DATA from {sender_id} with data length {data_length}")

                self._state = IDLE_STATE
                self._send_ack(sender_id)

        ################
        # Received ACK #
        ################
        elif msg == 'ACK':
            if self.id == target_id:
                # Simulate time it takes to transmite ACK message
                yield self.timeout(BYTE_TRANSMISSION_TIME * DATA_LENGTH["ACK"])
                # we can finally remove the data packet from the queue yeah
                self.log(f"Received ACK from {sender_id}")
                self._data_queue.pop(0)
                self._state = IDLE_STATE
                self._backoff_time = MIN_BACKOFF_TIME

            # Neigboard data transmission is done, we can send RRTSs
            else:
                for node_id in self._received_rts:
                    self._send_rrts(node_id)
