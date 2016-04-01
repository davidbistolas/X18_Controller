import controller
import midiprocessor

_ip = '192.168.0.108'

c = controller.BehringerController(_ip)
m = midiprocessor.MidiProcessor(c)
m.start()
