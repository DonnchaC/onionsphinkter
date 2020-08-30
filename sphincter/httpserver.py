import logging
from threading import Thread
from urllib.parse import urlparse, parse_qs
from sphincter.requestqueue import SphincterRequest, REQUEST_OPEN, REQUEST_CLOSE

from http.server import HTTPServer, BaseHTTPRequestHandler

class SphincterHTTPRequestHandler(BaseHTTPRequestHandler):
    def respond(self, code, message):
        self.send_response(code)
        self.end_headers()
        self.wfile.write(message)

    def do_GET(self):
        params = self.get_params

        if "action" not in params.keys():
            self.send_error(400, b"ACTION NOT SPECIFIED")
            return

        if params["action"] not in ["open"]:
            self.send_error(400, b"INVALID ACTION")
            return

        if "token" not in params.keys():
            self.respond(401, b"NO TOKEN")
            return

        if not self.server.user_manager.check_token(params["token"]):
            self.respond(401, b"TOKEN INVALID")
            return

        if params["action"] == "open":
            r = SphincterRequest(REQUEST_OPEN)
            self.server._request_queue.append(r)
            r.event.wait()
            if r.success:
                self.respond(200, b"UNLOCKED")
            else:
                self.respond(503, b"FAILED")
            return
        elif params["action"] == "test":
            self.respond(200, b"OK")
            return

    @property
    def get_params(self):
        parse_res = parse_qs(urlparse(self.path).query)
        params = {}
        for k in parse_res:
            params[k] = parse_res[k][0]
        return params

    def log_message(self, format, *args):
        logging.info("HTTP Request" + format % tuple(args))

class SphincterHTTPServer(HTTPServer):
    def __init__(self, address, request_queue, serial_handler, user_manager):
        self._request_queue = request_queue
        self.serial_handler = serial_handler
        self.user_manager = user_manager
        HTTPServer.__init__(self, address, SphincterHTTPRequestHandler)

class SphincterHTTPServerRunner(object):
    def __init__(self, address, request_queue, serial_handler, user_manager):
        self._address = address
        self._request_queue = request_queue
        self._serial_handler = serial_handler
        self._user_manager = user_manager

    def __call__(self):
        s = SphincterHTTPServer(self._address, self._request_queue, self._serial_handler, self._user_manager)
        logging.info("HTTP Server starting up")
        s.serve_forever()

    @classmethod
    def start_thread(cls, address, request_queue, serial_handler, user_manager):
        t = Thread(name="HTTPThread",
                   target=cls(address, request_queue, serial_handler, user_manager))
        t.daemon = True
        t.start()
