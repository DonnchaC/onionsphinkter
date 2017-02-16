from threading import Event, Thread
from time import sleep
import logging

REQUEST_OPEN = 1
REQUEST_CLOSE = 2

class SphincterRequest(object):
    def __init__(self, request_type):
        self.event = Event()
        self.request_type = request_type
        self.success = True

class SphincterRequestQueue(object):
    def __init__(self):
        self._items = []
        
    def append(self, request):
        self._items.append(request)

    def pop(self):
        return self._items.pop(0)
    
    @property
    def is_empty(self):
        return len(self._items) == 0
        
    def set_all(self, request_type):
        delete_items = []
        for r in self._items:
            if r.request_type == request_type:
                r.event.set()
                delete_items.append(r)

        for r in delete_items:
            self._items.remove(r)

class SphincterRequestHandler(Thread):
    def __init__(self, request_queue, serial_handler):
        self.request_queue = request_queue
        self.serial_handler = serial_handler
        Thread.__init__(self, name="RequestQueueWorkerThread")
        self.daemon = True

    def run(self):
        logging.info("RequestHandler Thread starting")
        while True:
            while not self.request_queue.is_empty:
                r = self.request_queue.pop()
                if r.request_type == REQUEST_OPEN:
                    logging.info("Opening Sphincter")
                    self.serial_handler.open()
                    self.serial_handler.open_event.wait()

                self.request_queue.set_all(r.request_type)
                r.event.set()

            logging.debug("request queue is empty")
            sleep(0.1)
