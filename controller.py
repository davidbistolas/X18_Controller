"""
Behringer OSC Mute Automation Controller
"""
import threading
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
        self.client = client
        self.server = server
        if callback is not None:
            self.callback = callback
        else:
            self.callback = self._empty_callback
        self.value = None
        self.server.addMsgHandler(self.address, self.handler)

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
        Send the message to the behringer.
        :param address:
        :param value:
        :return:
        """
        oscmsg = OSC.OSCMessage()
        oscmsg.setAddress(self.address)
        self.client.send(oscmsg)

    def set(self, value=None):
        """
        Send the message to the behringer.
        :param address:
        :param value:
        :return:
        """
        if value != self.value:
            oscmsg = OSC.OSCMessage()
            oscmsg.setAddress(self.address)
            if value != None:
                oscmsg.append(int(value))
            self.client.send(oscmsg)
        self.get()

    def _empty_callback(self, call, param, response, device):
        pass


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
        :param address:
        :param value:
        :return:
        """

        oscmsg = OSC.OSCMessage()
        oscmsg.setAddress(self.response_address)
        self.client.send(oscmsg)


class FaderElement(MixerElement):
    """
    Handle fader calls and responses.
    """

    def value_convert(self, value):
        return int(round(value * 1024)-1)


class MuteElement(MixerElement):
    """
    Handle mute calls and responses.
    """
    pass


class panElement(MixerElement):
    """
    Handle pan calls and responses.
    """

    def value_convert(self, value):
        return int(round(value * 100))


class BehringerController(threading.Thread):
    def __init__(self, ip, port=10024):
        self.server = OSC.OSCServer(("0.0.0.0", port))
        self.client = OSC.OSCClient(server=self.server)
        self.client.connect((ip, port))
        self.ready = False
        self.info = {'model': None, 'address': None, 'version': None, 'name': None}
        self.info_call = MixerElement("/xinfo", self.client, self.server, self.info_callback)
        self.snapshot_call = SnapElement("/-snap/load", self.client, self.server)
        self.mixer = {'ch': {}, 'fxsend': {}, 'bus': {}, 'rtn': {}, 'dca': {}, 'send': {}}

        for special_number in range(1, 5):
            fader = "/dca/" + str(special_number) + "/fader"
            mute = "/dca/" + str(special_number) + "/on"
            self.mixer["dca"][str(special_number)] = {}
            self.mixer["dca"][str(special_number)]['fader'] = FaderElement(fader, self.client, self.server)
            self.mixer["dca"][str(special_number)]['on'] = MuteElement(mute, self.client, self.server)

        for ch in range(1, 17):
            if ch < 10:
                channel_number = "0" + str(ch)
            else:
                channel_number = str(ch)

            fader = "/ch/" + channel_number + "/mix/fader"
            mute = "/ch/" + channel_number + "/mix/on"
            pan = "/ch/" + channel_number + "/mix/pan"

            self.mixer["ch"][channel_number] = {}
            self.mixer["ch"][channel_number]['fader'] = FaderElement(fader, self.client, self.server)
            self.mixer["ch"][channel_number]['on'] = MuteElement(mute, self.client, self.server)
            self.mixer["ch"][channel_number]['pan'] = panElement(pan, self.client, self.server)

        for rtn in range(1, 5):
            rtn_number = str(rtn)

            fader = "/rtn/" + rtn_number + "/mix/fader"
            mute = "/rtn/" + rtn_number + "/mix/on"
            pan = "/rtn/" + rtn_number + "/mix/pan"

            self.mixer["ch"][rtn_number] = {}
            self.mixer["ch"][rtn_number]['fader'] = FaderElement(fader, self.client, self.server)
            self.mixer["ch"][rtn_number]['on'] = MuteElement(mute, self.client, self.server)
            self.mixer["ch"][rtn_number]['pan'] = panElement(pan, self.client, self.server)

        for bus in range(1, 7):
            bus_number = str(bus)

            fader = "/bus/" + bus_number + "/mix/fader"
            mute = "/bus/" + bus_number + "/mix/on"
            pan = "/bus/" + bus_number + "/mix/pan"

            self.mixer["bus"][bus_number] = {}
            self.mixer["bus"][bus_number]['fader'] = FaderElement(fader, self.client, self.server)
            self.mixer["bus"][bus_number]['on'] = MuteElement(mute, self.client, self.server)
            self.mixer["bus"][bus_number]['pan'] = panElement(pan, self.client, self.server)

        for insert in ["fxsend", "rtn"]:
            for insert_number in range(1, 5):
                fader = "/" + insert + "/" + str(insert_number) + "/mix/fader"
                mute = "/" + insert + "/" + str(insert_number) + "/mix/on"
                self.mixer[insert][str(insert_number)] = {}
                self.mixer[insert][str(insert_number)]['fader'] = FaderElement(fader, self.client, self.server)
                self.mixer[insert][str(insert_number)]['on'] = MixerElement(mute, self.client, self.server)

        super(BehringerController, self).__init__()

    def run(self):
        """
        Thread run method
        :return:
        """
        # not happy with this solution- it's possible due to network latency that this will
        # get missed.
        self.get_info()
        self.server.serve_forever()

    def get_info(self):
        """
        Get mixer /info
        :return:
        """
        self.info_call.get()

    def info_callback(self, call, param, response, device):
        """
        info callback
        :param call:
        :param param:
        :param response:
        :param device:
        :return:
        """
        self.info['address'] = response[0]
        self.info['name'] = response[1]
        self.info['model'] = response[2]
        self.info['version'] = response[3]
        self.ready = True

    def snapshot(self, snapshot):
        """
        Sets the current snapshot
        :param snapshot:
        :return:
        """

        self.snapshot_call.set(snapshot)

    def setRtnFader(self, channel, amount):
        """
        Sets the Rtn level.
        :param channel:
        :param amount:
        :return:
        """
        c = str(channel)
        self.mixer["rtn"][c]["fader"].set(amount)

    def setRtnMute(self, channel, value):
        """
        Sets the DCA level.
        :param channel:
        :param amount:
        :return:
        """

        if value:
            amount = 0
        else:
            amount = 1

        c = str(channel)
        self.mixer["rtn"][c]["on"].set(amount)

    def setBusFader(self, channel, amount):
        """
        Sets the Bus level.
        :param channel:
        :param amount:
        :return:
        """
        c = str(channel)
        self.mixer["bus"][c]["fader"].set(amount)

    def setBusMute(self, channel, value):
        """
        Sets the DCA level.
        :param channel:
        :param amount:
        :return:
        """

        if value:
            amount = 0
        else:
            amount = 1

        c = str(channel)
        self.mixer["bus"][c]["on"].set(amount)

    def setFxSendFader(self, channel, amount):
        """
        Sets the DCA level.
        :param channel:
        :param amount:
        :return:
        """
        c = str(channel)
        self.mixer["fxsend"][c]["fader"].set(amount)

    def setFxSendMute(self, channel, value):
        """
        Sets the DCA level.
        :param channel:
        :param amount:
        :return:
        """

        if value:
            amount = 0
        else:
            amount = 1

        c = str(channel)
        self.mixer["fxsend"][c]["on"].set(amount)

    def setDCAFader(self, channel, amount):
        """
        Sets the DCA level.
        :param channel:
        :param amount:
        :return:
        """
        c = str(channel)
        self.mixer["dca"][c]["fader"].set(amount)

    def setDCAMute(self, channel, value):
        """
        Sets the DCA level.
        :param channel:
        :param amount:
        :return:
        """

        if value:
            amount = 0
        else:
            amount = 1

        c = str(channel)
        self.mixer["dca"][c]["on"].set(amount)

    def setChannelFader(self, channel, amount):
        """
        Sets the Channel level.
        :param channel:
        :param amount:
        :return:
        """
        if channel < 10:
            c = "0" + str(channel)
        else:
            c = str(channel)
        self.mixer["ch"][c]["fader"].set(amount)

    def setChannelMute(self, channel, value):
        """
        Sets the Channel level.
        :param channel:
        :param amount:
        :return:
        """
        if channel < 10:
            c = "0" + str(channel)
        else:
            c = str(channel)

        if value:
            amount = 0
        else:
            amount = 1

        self.mixer["ch"][c]["on"].set(amount)
