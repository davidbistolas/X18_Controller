import OSC


class MixerElement:
    """
    Mixer Element class. Represents a channel, return, dca, bus etc.
    """

    def __init__(self, address, client, server, callback=None):
        """
        Initializer
        :param address:
        :return:
        """
        self.address = address
        self.server = server
        if callback is not None:
            self.callback = callback
        else:
            self.callback = self._empty_callback
        self.value = None
        self.server.addMsgHandler(self.address, self.handler)
        self.client = client

    def value_convert(self, value):
        """
        Value conversion method. Override this.
        :param value:
        :return:
        """

        return value

    def handler(self, call, param, response, device):
        """
        Handler interceptor.

        :param call:
        :param param:
        :param response:
        :param device:
        :return:
        """
        self.value = self.value_convert(response[0])
        self.callback(call, param, response, device)

    def get(self):
        """
        Get the message from the behringer
        """
        oscmsg = OSC.OSCMessage()
        oscmsg.setAddress(self.address)
        self.send(oscmsg)

    def set(self, value=None):
        """
        Send the message to the behringer.
        :param value:
        :return:
        """
        #        if value != self.value:
        oscmsg = OSC.OSCMessage()
        oscmsg.setAddress(self.address)
        if value is not None:
            oscmsg.append(int(value))
        self.send(oscmsg)

    def _empty_callback(self, call, param, response, device):
        pass

    def send(self, message):
        """
        Send the OSC message

        """
#        self.message_queue.put(message)
        self.client.send(message)


class SnapElement(MixerElement):
    """
    Handle snapshots
    """

    def __init__(self, address, client, server, callback=None):
        """
        Initializer
        :param address:
        :return:
        """
        MixerElement.__init__(self, address, client, server, callback)
        self.response_address = "/-snap/index"
        self.server.addMsgHandler(self.response_address, self.handler)

    def get(self):
        """
        Send the message to the behringer.
        :return:
        """

        oscmsg = OSC.OSCMessage()
        oscmsg.setAddress(self.response_address)
        self.send(oscmsg)


class FaderElement(MixerElement):
    """
    Handle fader calls and responses.
    """

    def value_convert(self, value):
        return int(round(value * 1024) - 1)


class MuteElement(MixerElement):
    """
    Handle mute calls and responses.
    """
    pass


class PanElement(MixerElement):
    """
    Handle pan calls and responses.
    """

    def value_convert(self, value):
        return int(round(value * 100))
