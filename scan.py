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

    SCAN_DIR = ""
    STATUS = ["init"]
    BUTTONS={}

    def __init__(self, scanner_name):
        self.NAME = scanner_name

        self.check_scanner()

        if self.LIVE == "online":
            print(f"scanner: {self.NAME}")
            self.STATUS = self.get_status()

            [print(x) for x in self.STATUS]

    def set_scan_dir(self, path):
        self.SCAN_DIR = Path(path)
        print(f"Scan-target: {self.SCAN_DIR}")
        if not self.SCAN_DIR.exists():
            mkdir(self.SCAN_DIR)
            print(f"created {self.SCAN_DIR}")



    def get_file_name(self, suffix):
        return f'{self.SCAN_DIR}/{datetime.now().strftime("%Y_%m_%d_%H_%M_%S")}.{suffix}'

    def args_to_cmd(self, args):
        if "batch" in args.keys():
            line = f'scanimage' # --output="{get_file_name(args["format"])}"'
        else:
            line = f'scanimage --output="{get_file_name(args["format"])}"'

        if not "device" in args.keys():
            args["device"] = self.NAME
        kv = " ".join({(f'--{k}="{v}"') for k, v in args.items() if v is not None})
        k = " ".join({(f"--{k}") for k, v in args.items() if v is None})
        print(" ".join([line, k, kv]))
        return " ".join([line, k, kv])



    def check_scanner(self):
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
        proc = sub.Popen(
            [f"scanimage -d {self.NAME} -A"],
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE,
            shell=True,
        )

        return [
            x.strip(" ")
            for x in proc.stdout.read().decode("utf-8").split("\n")
            if "--" in x
        ]

    def add_key(self, button_name, args):
        self.BUTTONS[button_name] = args

    def check_button(self, line):
        button_name = line.split('[')[0]
        if button_name in self.BUTTONS.keys():
           print(f"Button {button_name} pressed")
           proc = sub.Popen(
            [self.args_to_cmd(self.BUTTONS[button_name])],
            stdin=PIPE,
            #stdout=PIPE,
            #stderr=PIPE,
            shell=True,
        )


    def read(self):
        fresh_status = self.get_status()
        diff = set(fresh_status) - set(self.STATUS)
        if len(diff) > 0:
            print(f"Diff: {diff}")
            [self.check_button(x.strip('-\[')) for x in diff ]

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
