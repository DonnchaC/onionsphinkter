#!/usr/bin/env python3

import sys

if sys.version_info[0] < 3:
    raise ImportError('Python < 3 is not supported.')

import logging
from time import sleep
from os import path
from sys import exit
from threading import Thread

from argparse import ArgumentParser

from sphincter.gpio_connection import SphincterGPIOHandler
from sphincter.requestqueue import SphincterRequestQueue, SphincterRequestHandler
from sphincter.httpserver import SphincterHTTPServerRunner
from sphincter.authentication import UserManager
from sphincter.authentication import random_token
from sphincter.config import SphincterConfig
import hooks

if __name__ == "__main__":
    aparser = ArgumentParser(prog="sphincterd",
                             description="Spincter control daemon")
    aparser.add_argument("--configfile", action="store",
                         default=path.join(path.abspath(path.dirname(__file__)), "sphincterd.conf"),
                         help="Path to configuration file")
    aparser.add_argument("--initdb", action="store_true", help="Create a new database.")
    aparser.add_argument("--test-hook", action="store", choices=["open", "closed", "failure"], help="Test hooks.")
    aparser.add_argument("--adduser", action="store", help="Add new user.")
    aparser.add_argument("--deluser", action="store", help="Delete existing user.")
    aparser.add_argument("--listusers", action="store_true", help="List all users.")
    args = aparser.parse_args()

    if args.test_hook is not None:
        import hooks
        if args.test_hook == "open":
            hooks.open_hook()
        elif args.test_hook == "closed":
            hooks.closed_hook()
        elif args.test_hook == "failure":
            hooks.failure_hook()
        else:
            print("unknown hook!")
            exit(1)
        exit(0)

    conf = SphincterConfig(args.configfile)
    config_params = conf.__dict__.keys()

    #if "device" not in config_params:
    #    logging.critical("device parameter not in config file")
    #    exit(1)

    if "loglevel" not in config_params:
        logging.critical("loglevel parameter not in config file")
        exit(1)

    # parse loglevel
    if conf.loglevel == "DEBUG":
        loglevel = logging.DEBUG
    elif conf.loglevel == "INFO":
        loglevel = logging.INFO
    elif conf.loglevel == "WARNING":
        loglevel = logging.WARNING
    elif conf.loglevel == "ERROR":
        loglevel = logging.ERROR
    elif conf.loglevel == "CRITICAL":
        loglevel = logging.CRITICAL
    else:
        logging.critical("Unknown loglevel {}".format(conf.loglevel))
        exit(1)

    logfile = "/var/log/sphincterd.log"
    logging.basicConfig(level=logging.INFO,
                        filename=logfile,
                        format='%(asctime)s - %(levelname)8s - %(threadName)s/%(funcName)s - %(message)s',
                        datefmt="%Y-%m-%d %H:%M")
    logging.info("ohai, this is sphincterd")

    if "address" not in config_params:
        logging.critical("address parameter not in config file")
        exit(1)

    listen_address = conf.address

    if "portnumber" not in config_params:
        logging.critical("portnumber parameter not in config file")
        exit(1)

    try:
        listen_port = int(conf.portnumber)
    except ValueError:
        logging.critical("Could not parse port number parameter: {}".format(conf.portnumber))
        exit(1)

    s = SphincterGPIOHandler()

    um = UserManager(dbpath="sqlite:///{}".format(path.join(path.abspath(path.dirname(__file__)), "sphincter.sqlite")))

    if args.initdb:
        um.create_tables()
        print("Database initialized: {}".format(um.engine.url))
        exit(0)

    if args.adduser:
        token = random_token(32).encode('utf-8')
        user = um.add_user(args.adduser, token)
        if user is not None:
            print("Adding user {}".format(user.email))
            exit(0)
        else:
            print("User already exits!")
            exit(1)

    if args.deluser:
        user = um.del_user(args.deluser)
        if user is not None:
            print("Delete user {}".format(user.email))
            exit(0)
        else:
            print("User not found!")
            exit(1)

    if args.listusers:
        users = um.get_users()
        for user in users:
            print("{}".format(user.email))
        print("Found {} users".format(users.count()))
        exit(0)

    q = SphincterRequestQueue()
    r = SphincterRequestHandler(q, s)
    r.start()

    print("Log to {}".format(logfile))
    print("Start webserver on {}:{}".format(listen_address, listen_port))
    SphincterHTTPServerRunner.start_thread((listen_address, listen_port), q, s, um)

    # run timer hook
    class TimerThread(Thread):
        def __init__(self, serial_handler):
            self._serial_handler = serial_handler
            Thread.__init__(self, name="TimerThread")
            self.daemon = True
        
        def run(self):
            while True:
                hooks.timer_hook(self._serial_handler.state)
                sleep(300)
    
    tthread = TimerThread(s)
    tthread.start()
    
    # sleep until CTRL-C, then quit.
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        logging.info("shutting down sphincterd, kthxbai")
