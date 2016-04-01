from simplecoremidi import MIDIDestination
import threading


class MidiReceiver(threading.Thread):
    """
    Threaded, queue enabled midi reciever
    """

    def __init__(self, midi_queue, driver_name):
        """
        Init Method
        """
        self.midi_driver_name = driver_name
        self.midi_source = MIDIDestination(driver_name)
        self.queue = midi_queue
        self.active = True
        super(MidiReceiver, self).__init__()
        print "Setting up Midi Driver Queue '", driver_name, "'"

    def run(self):
        """
        Run Method
        """
        print "Midi Driver", self.midi_driver_name, "is now starting..."
        while self.active:
            midi_data = self.midi_source.recv()
            if midi_data:
                self.queue.put(midi_data)
