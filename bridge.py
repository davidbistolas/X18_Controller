import controller
import midireceiver

if __name__ == '__main__':
    controller = controller.BehringerController()
    controller.start()
    controller.find_mixer()
    print "Found", controller.mixer_name
    service = midireceiver.MidiReceiver(controller,controller.mixer_name)
    try:
        service.start()
    except (KeyboardInterrupt, SystemExit):
        raise