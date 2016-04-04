import controller
import midiprocessor
import rumps

_ip = '192.168.0.108'

__appname__ = "OSC Bridge"


class Bridge(rumps.App):

    def __init__(self, driver_name="XAir OSC Bridge", ip='0.0.0.0'):
        """q
        midi->OSC bridge
        :param driver_name:  The midi name of the bridge. This will
                      show up in Logic
        :param ip:    Mixer to connect to
        """

        self.driver_name = driver_name
        icon = None
        menu = ["Start", "Stop", "Reset"]
        self.ip = ip
        self.service = None
        self.controller = None
        super(Bridge, self).__init__(driver_name, driver_name, icon, menu, quit_button=None)

    @rumps.clicked("Start")
    def run_bridge(self, _):
        """ Starts up the bridge """
        self.controller = controller.BehringerController(self.ip)
        self.service = midiprocessor.MidiProcessor(self.controller)
        self.service.start()


    @rumps.clicked("Stop")
    def stop_bridge(self, _):
        """ Stops the bridge """
        if self.service:
            self.service.stop()
            del self.service
            del self.controller

    @rumps.clicked("Reset")
    def stop_bridge(self, _):
        """ Stops the bridge """
        if self.service:
            self.service.stop()

    # noinspection PyBroadException\\

    @rumps.clicked("Exit")
    def quit_app(self, _):
        try:
            self.service.stop()
        except Exception, e:
            print e
        rumps.quit_application()


if __name__ == '__main__':
    #repeater = Bridge()
    #repeater.run()
    controller = controller.BehringerController()
    service = midiprocessor.MidiProcessor(controller)
    service.start()
