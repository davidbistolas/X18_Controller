import threading


class BehringerSender(threading.Thread):
    """
    Sends data to the behnriger by way of the Queue
    """

    def __init__(self, client, queue):
        """
        Initialize.
        """
        self.client = client
        self.message_queue = queue
        self.active = False
        super(BehringerSender, self).__init__()

        self.start_sending()

    def start_sending(self):
        """
        Start listening to midi
        :return:
        """
        self.active = True

    def stop_sending(self):
        """
        Start listening to midi
        :return:
        """
        self.active = False

    def run(self):
        """
        Run the OSC Sender
        :return:
        """

        while self.active:
            message = self.message_queue.get()
            self.client.send(message)
            self.message_queue.task_done()
