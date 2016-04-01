from midireceiver import MidiReceiver
import threading
import Queue

CONTROL_OFFSET = 177
NOTE_ON_OFFSET = 144
NOTE_OFF_OFFSET = 128

# C0
CHANNEL_MUTE = 24
# C1
DCA_MUTE = 48
FX_MUTE = 52
RTN_MUTE = 56
# C3
MUTE_GROUP = 60


class MidiProcessor(threading.Thread):
    """
    Midi receiver server
    """

    def __init__(self, osc_controller, midi_driver_name="Behringer XAir OSC"):
        """
        Initialize MidiReceiver
        :return:
        """
        self.listen = True
        self.osc_controller = osc_controller
        self.midi_queue = Queue.Queue()
        self.midi_source = MidiReceiver(self.midi_queue, midi_driver_name)
        self.midi_source.start()
        super(MidiProcessor, self).__init__()
        self.start_listening()

    def start_listening(self):
        """
        Start listening to midi
        :return:
        """
        self.listen = True

    def stop_listening(self):
        """
        Start listening to midi
        :return:
        """
        self.listen = False

    def parse_midi(self, message):
        """
        Parse the midi message
        :param message:
        :return:
        """

        m_type = message[0]

        # a program change on ANY midi channel changes the snapshot
        # the snapshot must exist on the device. we're not wizards, you
        # know.
        if m_type in range(CONTROL_OFFSET, CONTROL_OFFSET + 16):
            if len(message) == 8:
                self.osc_controller.snapshot(message[7])
            if len(message) == 3:
                channel = (CONTROL_OFFSET - message[0]) + 1
                controller = message[1]
                value = message[2]
                # 7: volume change
                if controller == 7:
                    value = (value * 8)
                    self.osc_controller.set_channel_fader(channel, value)
                # 8: Pan
                if controller == 10:
                    value = int((round(value, 3) / 127) * 100)
                    self.osc_controller.set_channel_pan(channel, value)
                # 14: DCA volume change
                if controller == 14:
                    value = (value * 8) - 1
                    self.osc_controller.set_dca_fader(channel, value)
                # 15: FxSend Volume Change
                if controller == 15:
                    value = (value * 8) - 1
                    self.osc_controller.set_fxsend_fader(channel, value)
                # 16: Bus Volume Change
                if controller == 16:
                    value = (value * 8) - 1
                    self.osc_controller.set_bus_fader(channel, value)
                # 17: Rtn Volume Change
                if controller == 16:
                    value = (value * 8) - 1
                    self.osc_controller.set_return_fader(channel, value)
        # mute on
        if m_type in range(NOTE_ON_OFFSET, NOTE_ON_OFFSET + 16):
            if message[1] in range(MUTE_GROUP, MUTE_GROUP + 4):
                channel = message[1] - (MUTE_GROUP - 1)
                self.osc_controller.set_mute_group_mute(channel, 0)

            if message[1] in range(CHANNEL_MUTE, CHANNEL_MUTE + 16):
                channel = message[1] - (CHANNEL_MUTE - 1)
                self.osc_controller.set_channel_mute(channel, 1)

            if message[1] in range(FX_MUTE, FX_MUTE + 4):
                channel = message[1] - (FX_MUTE - 1)
                self.osc_controller.set_fxsend_mute(channel, 1)

            if message[1] in range(DCA_MUTE, DCA_MUTE + 4):
                channel = message[1] - (DCA_MUTE - 1)
                self.osc_controller.set_dca_mute(channel, 1)

            if message[1] in range(RTN_MUTE, RTN_MUTE + 4):
                channel = message[1] - (RTN_MUTE - 1)
                self.osc_controller.set_return_mute(channel, 1)
        # mute off
        if m_type in range(NOTE_OFF_OFFSET, NOTE_OFF_OFFSET + 16):
            if message[1] in range(MUTE_GROUP, MUTE_GROUP + 4):
                channel = message[1] - (MUTE_GROUP - 1)
                self.osc_controller.set_mute_group_mute(channel, 1)

            if message[1] in range(CHANNEL_MUTE, CHANNEL_MUTE + 16):
                channel = message[1] - (CHANNEL_MUTE - 1)
                self.osc_controller.set_channel_mute(channel, 0)

            if message[1] in range(FX_MUTE, FX_MUTE + 4):
                channel = message[1] - (FX_MUTE - 1)
                self.osc_controller.set_fxsend_mute(channel, 0)

            if message[1] in range(DCA_MUTE, DCA_MUTE + 4):
                channel = message[1] - (DCA_MUTE - 1)
                self.osc_controller.set_dca_mute(channel, 0)

            if message[1] in range(RTN_MUTE, RTN_MUTE + 4):
                channel = message[1] - (RTN_MUTE - 1)
                self.osc_controller.set_return_mute(channel, 0)

    def run(self):
        """
        Run the midi server
        :return:
        """

        while self.listen:
            message = self.midi_queue.get()
            self.parse_midi(message)
            self.midi_queue.task_done()
