import zmq

import time
import PongProcExample.base as base

host = '127.0.0.1'
port = 5678


def ping():
    """Sends ping requests and waits for replies."""
    context = zmq.Context()
    sock = context.socket(zmq.REQ)
    sock.connect('tcp://%s:%s' % (host, port))

    for i in range(5):
        sock.send_json(['ping', i])
        rep = sock.recv_json()
        print('Ping got reply:', rep)

    sock.send_json(['plzdiekthxbye', None])


class PongProc(base.ZmqProcess):
    """
    Main processes for the Ponger. It handles ping requests and sends back
    a pong.

    """
    def __init__(self, bind_addr):
        super().__init__()

        self.bind_addr = bind_addr
        self.rep_stream = None
        self.ping_handler = PingHandler()
        self.seconds_handler = SecHandler()

    def setup(self):
        """Sets up PyZMQ and creates all streams."""
        super().setup()

        # Create the stream and add the message handler
        self.rep_stream, _ = self.stream(zmq.REP, self.bind_addr, bind=True)
        self.rep_stream.on_recv(RepStreamHandler(self.rep_stream, self.stop,
                                                 self.ping_handler, self.seconds_handler))

    def run(self):
        """Sets up everything and starts the event loop."""
        self.setup()
        self.loop.start()

    def stop(self):
        """Stops the event loop."""
        self.loop.stop()


class RepStreamHandler(base.MessageHandler):
    """ Handels messages arrvinge at the PongProc s REP stream."""
    def __init__(self, rep_stream, stop, ping_handler, seconds_handler):
        super().__init__()
        self._rep_stream = rep_stream
        self._stop = stop
        self._ping_handler = ping_handler
        self._seconds_handler = seconds_handler

    def ping(self, data):
        """Send back a pong."""
        rep = self._ping_handler.make_pong(data)
        self._rep_stream.send_json(rep)

    def seconds(self, data):
        print('going to fake schedule here at {}'.format(data))
        rep = self._seconds_handler.schedule(data)
        self._rep_stream.send_json(rep)

    def plzdiekthxbye(self, data):
        """Just calls :meth:`PongProc.stop`."""
        self._stop()


class PingHandler(object):

    def make_pong(self, num_pings):
        """Creates and returns a pong message."""
        print('Pong got request number %s' % num_pings)

        return ['pong', num_pings]

class SecHandler(object):

    def schedule(self, secdelta):
        print('fake scheduled at {} seconds'.format(secdelta))
        return ['Ok']

if __name__ == '__main__':
    pong_proc = PongProc(bind_addr=(host, port))
    st = pong_proc.start()
    ping()

    pong_proc.join()