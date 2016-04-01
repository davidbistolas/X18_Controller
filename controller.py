"""
Behringer OSC Mute Automation Controller
"""
import threading
import OSC
import Queue
from x18mixer import MixerElement, MuteElement, FaderElement, SnapElement, PanElement
from behringersender import BehringerSender


class BehringerController(threading.Thread):
    def __init__(self, ip, port=10024):
        self.server = OSC.ThreadingOSCServer(("0.0.0.0", port))
        self.client = OSC.OSCClient(server=self.server)
        self.client.connect((ip, port))
        self.queue = Queue.Queue()
        self.osc_sender = BehringerSender(self.client, self.queue)
        print "Starting osc_sender"
        self.osc_sender.start()
        print "Setting up listeners"
        self.ready = False
        self.info = {
            'model': None,
            'address': None,
            'version': None,
            'name': None}
        self.info_call = MixerElement(
            "/xinfo", self.queue, self.server, self.info_callback)
        self.snapshot_call = SnapElement(
            "/-snap/load", self.queue, self.server)
        self.mixer = {
            'ch': {},
            'fxsend': {},
            'bus': {},
            'rtn': {},
            'dca': {},
            'send': {},
            'mutegrp': {}}

        for special_number in range(1, 5):
            fader = "/dca/" + str(special_number) + "/fader"
            mute = "/dca/" + str(special_number) + "/on"
            self.mixer["dca"][str(special_number)] = {}
            self.mixer["dca"][
                str(special_number)]['fader'] = FaderElement(
                fader, self.queue, self.server)
            self.mixer["dca"][
                str(special_number)]['on'] = MuteElement(
                mute, self.queue, self.server)

        for ch in range(1, 17):
            if ch < 10:
                channel_number = "0" + str(ch)
            else:
                channel_number = str(ch)

            fader = "/ch/" + channel_number + "/mix/fader"
            mute = "/ch/" + channel_number + "/mix/on"
            pan = "/ch/" + channel_number + "/mix/pan"

            self.mixer["ch"][channel_number] = {}
            self.mixer["ch"][channel_number]['fader'] = FaderElement(
                fader, self.queue, self.server)
            self.mixer["ch"][channel_number]['on'] = MuteElement(
                mute, self.queue, self.server)
            self.mixer["ch"][channel_number]['pan'] = PanElement(
                pan, self.queue, self.server)

        for rtn in range(1, 5):
            rtn_number = str(rtn)

            fader = "/rtn/" + rtn_number + "/mix/fader"
            mute = "/rtn/" + rtn_number + "/mix/on"
            pan = "/rtn/" + rtn_number + "/mix/pan"

            self.mixer["ch"][rtn_number] = {}
            self.mixer["ch"][rtn_number]['fader'] = FaderElement(
                fader, self.queue, self.server)
            self.mixer["ch"][rtn_number]['on'] = MuteElement(
                mute, self.queue, self.server)
            self.mixer["ch"][rtn_number]['pan'] = PanElement(
                pan, self.queue, self.server)

        for bus in range(1, 7):
            bus_number = str(bus)

            fader = "/bus/" + bus_number + "/mix/fader"
            mute = "/bus/" + bus_number + "/mix/on"
            pan = "/bus/" + bus_number + "/mix/pan"

            self.mixer["bus"][bus_number] = {}
            self.mixer["bus"][bus_number]['fader'] = FaderElement(
                fader, self.queue, self.server)
            self.mixer["bus"][bus_number]['on'] = MuteElement(
                mute, self.queue, self.server)
            self.mixer["bus"][bus_number]['pan'] = PanElement(
                pan, self.queue, self.server)

        for insert in ["fxsend", "rtn"]:
            for insert_number in range(1, 5):
                fader = "/" + insert + "/" + str(insert_number) + "/mix/fader"
                mute = "/" + insert + "/" + str(insert_number) + "/mix/on"
                self.mixer[insert][str(insert_number)] = {}
                self.mixer[insert][
                    str(insert_number)]['fader'] = FaderElement(
                    fader, self.queue, self.server)
                self.mixer[insert][
                    str(insert_number)]['on'] = MixerElement(
                    mute, self.queue, self.server)

        for mutegroup_number in range(1, 5):
            mute = "/config/mute/" + str(mutegroup_number)
            self.mixer["mutegrp"][str(mutegroup_number)] = {}
            self.mixer["mutegrp"][
                str(mutegroup_number)]['on'] = MixerElement(
                mute, self.queue, self.server)

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
        self.info['call'] = call
        self.info['param'] = param
        self.info['device'] = device
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

    def set_return_fader(self, channel, amount):
        """
        Sets the Rtn level.
        :param channel:
        :param amount:
        :return:
        """
        c = str(channel)
        self.mixer["rtn"][c]["fader"].set(amount)

    def set_return_mute(self, channel, value):
        """
        Sets the DCA level.
        :param channel:
        :param value:
        :return:
        """

        if value:
            amount = 0
        else:
            amount = 1

        c = str(channel)
        self.mixer["rtn"][c]["on"].set(amount)

    def set_bus_fader(self, channel, amount):
        """
        Sets the Bus level.
        :param channel:
        :param amount:
        :return:
        """
        c = str(channel)
        self.mixer["bus"][c]["fader"].set(amount)

    def set_bus_mute(self, channel, value):
        """
        Sets the DCA level.
        :param channel:
        :param value:
        :return:
        """

        if value:
            amount = 0
        else:
            amount = 1

        c = str(channel)
        self.mixer["bus"][c]["on"].set(amount)

    def set_fxsend_fader(self, channel, amount):
        """
        Sets the DCA level.
        :param channel:
        :param amount:
        :return:
        """
        c = str(channel)
        self.mixer["fxsend"][c]["fader"].set(amount)

    def set_fxsend_mute(self, channel, value):
        """
        Sets the DCA level.
        :param channel:
        :param value:
        :return:
        """

        if value:
            amount = 0
        else:
            amount = 1

        c = str(channel)
        self.mixer["fxsend"][c]["on"].set(amount)

    def set_dca_fader(self, channel, amount):
        """
        Sets the DCA level.
        :param channel:
        :param amount:
        :return:
        """
        c = str(channel)
        self.mixer["dca"][c]["fader"].set(amount)

    def set_mute_group_mute(self, channel, value):
        """
        Activates a mute group.
        :param channel:
        :param value:
        :return:
        """

        if value:
            amount = 0
        else:
            amount = 1

        c = str(channel)
        self.mixer["mutegrp"][c]["on"].set(amount)

    def set_dca_mute(self, channel, value):
        """
        Sets the DCA level.
        :param channel:
        :param value:
        :return:
        """

        if value:
            amount = 0
        else:
            amount = 1

        c = str(channel)
        self.mixer["dca"][c]["on"].set(amount)

    def set_channel_fader(self, channel, amount):
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

    def set_channel_mute(self, channel, value):
        """
        Sets the Channel level.
        :param channel:
        :param value:
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

    def set_channel_pan(self, channel, amount):
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
        self.mixer["ch"][c]["pan"].set(amount)
