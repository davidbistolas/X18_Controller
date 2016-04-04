#from simplecoremidi import MIDIDestination
import threading
import itertools
import rtmidi

def split_seq(iterable, size):
    """Little hack to split iterables up"""
    it = iter(iterable)
    item = list(itertools.islice(it, size))
    while item:
        yield item
        item = list(itertools.islice(it, size))

CONTROL_OFFSET = 176
PROGRAM_OFFSET = 192

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


class MidiInputHandler:
    """Midi Input Handler"""

    def __init__(self, osc_controller):
        self.osc_controller = osc_controller

    def __call__(self, event, data=None):
        message, deltatime = event
        self.parse_midi(message)

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

        if m_type in range(PROGRAM_OFFSET, PROGRAM_OFFSET + 16):
            self.osc_controller.snapshot(message[1])

        if m_type in range(CONTROL_OFFSET, CONTROL_OFFSET + 16):
            if len(message) == 3:
                channel = (message[0] - CONTROL_OFFSET) + 1
                controller = message[1]
                value = message[2]
                # 14: DCA volume change
                if controller == 14:
                    value = (value * 8) - 1
                    self.osc_controller.set_dca_fader(channel, value)
                # 15: FxSend Volume Change
                if controller == 15:
                    value = (value * 8) - 1
                    self.osc_controller.set_fxsend_fader(channel, value)
                # 17: Rtn Volume Change
                if controller == 17:
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

class MidiReceiver(threading.Thread):
    """
    Threaded, queue enabled midi reciever
    """

    def __init__(self, osc_controller, driver_name):
        """
        Init Method
        """
        self.midi_driver_name = driver_name
        midiin = rtmidi.MidiIn()
        self.rtmidiin = midiin.open_virtual_port(driver_name)
        self.rtmidiin.set_callback(MidiInputHandler(osc_controller))
        self.active = False
        super(MidiReceiver, self).__init__()

    def run(self):
        """
        Run Method
        """
        print "Midi Driver", self.midi_driver_name, "is now starting..."
        self.active = True
    def stop(self):
        """
        Stop the listener
        """
        print "Midi Driver", self.midi_driver_name, "is shutting down..."
        self.active = False

