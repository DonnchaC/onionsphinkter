import logging
from threading import Thread, Event
from time import sleep

from RPi import GPIO

import hooks

class SphincterGPIOHandler:
    """
    Encapsulate Sphincter's Serial connection.
    """
    def __init__(self, unlock_pin=10):
        # init events
        self.open_event = Event()
        self._unlock_pin = unlock_pin

        # init GPIO Pins
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self._unlock_pin, GPIO.OUT)

    def open(self):
        """
        send open command to sphincter
        """
        GPIO.output(self._unlock_pin, GPIO.HIGH)
        logging.info("opening sphincter")
        sleep(0.15)
        GPIO.output(self._unlock_pin, GPIO.LOW)
        self.open_event.set()
        self.open_event.clear()

    def close(self):
        """
        send close command to sphincter
        """
        pass

    @property
    def state(self):
        return "UNCERTAIN"
