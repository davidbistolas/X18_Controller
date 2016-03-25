import controller
import time
#_ip="0.0.0.0"
_ip='10.5.0.126'
_port=10024

c = controller.BehringerController(_ip)
#c.ping()
#c.unmuteGroup(1)
#c.unmuteFx(1)
#c.muteChannel(1)
#c.setDCAFader(1,768)
#c.setChannelFader(1, 900)
#c.setFxFader(1, 300)
#c.setRtnFader(1,400)
#c.muteRtn(1)
#c.load_snapshot(1)
c.start()
# THIS will live in the midi loop.s
while True:
    if c.ready:
        c.setChannelFader(1,768)
        time.sleep(.1)
