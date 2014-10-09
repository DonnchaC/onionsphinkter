import logging
from threading import Thread, Event
from time import sleep

from serial import Serial, SerialException

class SphincterReader:
    """
    Read Sphincter state forever
    """
    def __init__(self, open_event, close_event, serial_handler):
        self.open_event = open_event
        self.close_event = close_event
        self.serial_handler = serial_handler
        
    def __call__(self):
        logging.info("starting reader thread")
        while True:
            data = self.serial_handler._serial.readline().strip()
            logging.info("read data %s" % data)
            
class SphincterReconnectReader(SphincterReader):
    """
    Read Sphincter state forever and reconnect if it disconnects.
    """
    def __call__(self):
        while True:
            try:
                SphincterReader.__call__(self)
            except SerialException:
                logging.warn("sphincter disconnected, trying to reconnect")
                self.serial_handler._serial.close()
                sleep(5)
                while True:
                    try:
                        self.serial_handler._serial.open()
                        break
                    except OSError:
                        logging.warn("reconnect failed, retrying...")
                        sleep(5)

class SphincterSerialHandler:
    """
    Encapsulate Sphincter's Serial connection.
    """
    def __init__(self, device='/dev/sphincter', baudrate=9600):
        # init serial connection
        self._serial = Serial()
        self._serial.baudrate = baudrate
        self._serial.port = device
        
        # init events
        self.closed_event = Event()
        self.open_event = Event()
        
        # init reader thread
        self._reader_thread = Thread(target=SphincterReconnectReader(self.open_event, self.closed_event, self),
                                     name="ReaderThread")
        # set daemon flag so the reader works in the background
        self._reader_thread.daemon = True

    def connect(self):
        """
        Connect to sphincter and start reader thread
        """
        self.disconnect()
        self._serial.open()
        self._reader_thread.start()
        
    def disconnect(self):
        """
        close serial connection to sphincter
        """
        if self._serial.isOpen():
            self._serial.close()
            
    def open(self):  
        """
        send open command to sphincter
        """
        self._serial.write(b"o")
        logging.info("sent OPEN")
        
    def close(self):
        """
        send close command to sphincter
        """
        self._serial.write(b"c")
        logging.info("sent CLOSE")
        
    def reset(self):
        """
        send reset command to sphincter
        """
        self._serial.write(b"r")
        logging.info("sent RESET")