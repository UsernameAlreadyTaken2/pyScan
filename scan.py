#! /usr/bin/env python
import subprocess as sub
from subprocess import PIPE
from datetime import datetime
import time
from pathlib import Path
import re

# TODO
# REGEX on STATUS --> "--(?P<arg>([a-z0-9--]*)) *(?P<info>.*) \[(?P<value>(.*))\]"


# SCANNER COMMANDS
class scanner:

    SCAN_DIR = ""            # target-dir for scanned data
    STATUS = ["init"]        # status-list with one information per line
    BUTTONS={}               # Buttons-dict: see "add_buttons" for reference

    def __init__(self, scanner_name):
        # Scanner Name for direct adressing
        self.NAME = scanner_name        
        # check if online
        self.check_scanner()
        if self.LIVE == "online":
            print(f"scanner: {self.NAME}")
            self.STATUS = self.get_status()
            # print all information to screen
            [print(x) for x in self.STATUS]

    def set_scan_dir(self, path):
        """Sets target scan-folder
        uses string as path, may accept pathlib.Path in future
        """
        self.SCAN_DIR = Path(path)
        print(f"Scan-target: {self.SCAN_DIR}")
        if not self.SCAN_DIR.exists():
            mkdir(self.SCAN_DIR)
            print(f"created {self.SCAN_DIR}")



    def get_file_name(self, suffix):
        """returns a unique file-name
        creates a filename wich leads to scan_dir with Datetime and given suffix
        """
        return f'{self.SCAN_DIR}/{datetime.now().strftime("%Y_%m_%d_%H_%M_%S")}.{suffix}'

    def args_to_cmd(self, args):
        """creates a scanimage-command
        in args, a dict is needed.
        some comands are directly linked to the fujitsu, due to lack of other devices, feel free to contribute!
        """
        if "batch" in args.keys(): # batch is not compatible with --output, 
            line = f'scanimage'
        else:
            line = f'scanimage --output="{get_file_name(args["format"])}"'

        if not "device" in args.keys():
            args["device"] = self.NAME
        # append all keys with values to a list of args
        kv = " ".join({(f'--{k}="{v}"') for k, v in args.items() if v is not None})
        # if value is none, use key as binary switch
        k = " ".join({(f"--{k}") for k, v in args.items() if v is None})
        # print as debug line
        print(" ".join([line, k, kv]))
        return " ".join([line, k, kv])

    def check_scanner(self):
        """checks availiability of scanners
        returns "online" or "offline" and sets self.LIVE
        """
        # call subprocess with getting a list of all scanners
        proc = sub.Popen(
            [f"scanimage -L"],
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE,
            shell=True,
        )

        if self.NAME in proc.stdout.read().decode("utf-8"):
            self.LIVE = "online"
            print(f"{self.NAME} is online")
            return "online"
        else:
            self.LIVE = "offline"
            print(f"{self.NAME} is offline")
            return "offline"

    def get_status(self):
        """get current system info for actual device
        scanimage -d <DEVICE> -A returns a full set of information
        """
        proc = sub.Popen(
            [f"scanimage -d {self.NAME} -A"],
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE,
            shell=True,
        )

        return [
            x.strip(" ") # remove leading and trailing spaces
            for x in proc.stdout.read().decode("utf-8").split("\n")
            if "--" in x # only lines with -- as commands, remove help-lines
        ]

    def add_key(self, button_name, args):
        """Scanner-Buttons-function
        If there are physical buttons on the device and they appear in status, the name of the button can trigger any events.
        usage: scn.add_key("scan", {"source":"ADF Duplex",...})
        """
        self.BUTTONS[button_name] = args

    def check_button(self, line):
        """run the command with linked set of arguments when button-push was detected
        
        """
        # in my case, line would be: --scan[=(yes|no)] [yes] [hardware]
        button_name = line.strip('-').split('[')[0]
        
        if button_name in self.BUTTONS.keys():
           print(f"Button {button_name} pressed")
            # run subprocess with line build from args in the BUTTONS-dict
           proc = sub.Popen(
            [self.args_to_cmd(self.BUTTONS[button_name])],
            stdin=PIPE,
            #stdout=PIPE,
            #stderr=PIPE,
            shell=True,
        )


    def read(self):
        # poll status
        fresh_status = self.get_status()
        # get only difference
        diff = set(fresh_status) - set(self.STATUS)
        if len(diff) > 0:
            print(f"Diff: {diff}")
            # only if there is a diff, check that buttons
            [self.check_button(x) for x in diff if "hardware" in x]

            self.STATUS = fresh_status

        return


# SCRIPT FUNCTIONS

if __name__ == "__main__":

    A4_WIDTH, A4_HEIGHT = 210, 297

    # start init
    args_scan = {
        "source": "ADF Duplex",
        "mode": "Color",
        "resolution": 300,
        "page-width": A4_WIDTH,
        "page-height": A4_HEIGHT,
        "format": "pdf",
        "batch":"/home/pi/paperless-ngx/consume/scan_%d.pdf",
        "progress": None,
        #"verbose": None,
    }

    print("init scanner")
    scn = scanner("fujitsu:fi-6130dj:446340")
    scn.set_scan_dir("/home/pi/paperless-ngx/consume/")

    scn.add_key("scan", args_scan)
    scn.add_key("mail", args_scan)

    print(scn.get_file_name("png"))

    while 1:
        if scn.LIVE == "online":
            scn.read()
        else:
            print("wait..")
            time.sleep(10)
            scn.check_scanner()


    exit(0)
