#! /usr/bin/env python
import subprocess as sub
from subprocess import PIPE

import tomlkit
import time
import re
import pathlib


def get_all_scanners():
    # run a subprocess to scanimages as formatted list: return only device-name
    proc = sub.Popen(
        [f"scanimage -f %d%n"],
        stdin=PIPE,
        stdout=PIPE,
        stderr=PIPE,
        shell=True,
    )

    error = proc.stderr.read().decode("utf-8")

    if error != "":
        print(error)
        return "error"

    return proc.stdout.read().decode("utf-8").split("\n")

def line_to_dict(x:str):
    regexp = r'--(?P<key>[a-z0-9-]*)[ \[](?P<info>.*?)[\] ]*?\[(?P<value>.*?)\] ?(?P<group>\[.*\])?'

    return re.match(regexp, x).groupdict()

def check(scanner:dict):

    proc = sub.Popen(
        [f'scanimage -d {scanner["device"]} -A --format="pnm"'],
        #stdin=PIPE,
        stdout=PIPE,
        stderr=PIPE,
        shell=True,
    )

    error = proc.stderr.read().decode("utf-8")

    if error != "":
        print(error)
        return "error"


    status = proc.stdout.read().decode("utf-8").split("\n")

    sensors = [line_to_dict(x.strip(" ")) # remove leading and trailing spaces
    for x in status
    if scanner["sensors"] in x ]# only lines with sensor-data

    sensors_dict = {item['key']:item for item in sensors}

    if len(sensors_dict) == 0:
        return status

    return sensors_dict

def __create_device_toml__():
    # run scanimage -L

    # if scanners found, create a document named "scanners.toml"
    # if such a document exists, name "scanners_DATETIME.toml"

    doc = tomlkit.document()
    doc.add(tomlkit.comment("SCANNER-List from SANE"))
    doc.add(tomlkit.nl)

    doc["title"] = "devices"

def check_devices():

    proc = sub.Popen(
        [f'lsusb'],
        #stdin=PIPE,
        stdout=PIPE,
        stderr=PIPE,
        shell=True,
    )

    error = proc.stderr.read().decode("utf-8")

    if error != "":
        print(error)
        return "error"


    return proc.stdout.read().decode("utf-8").split("\n")

def process(scanner):
    status = check(scanner)

    try:
        for action_name, action in scanner["actions"].items():

            matching_triggers = [status[key]["value"] == value for key,value in action.items()]

            if all(matching_triggers):
                action_commando = scanner["commandos"][action_name]
                print(f'action {action_name}: run { action_commando }')

                if action_commando.startswith("scanimage"):
                    proc = sub.Popen(
                        [action_commando],
                        #stdin=PIPE,
                        #stdout=PIPE,
                        #stderr=PIPE,
                        shell=True,
                        )


    except Exception as e:
        #print(status)
        print(f"Error: {e}")

def __backup__():
    A4_WIDTH, A4_HEIGHT = 210, 297

    scanjob={
        # standard
        "source":["ADF Front","ADF Back","ADF Duplex"][-1],
        "mode": ["Lineart","Halftone","Gray","Color"][-1],
        "resolution":300, #50..600 dpi
        # geometry
        "page-width": A4_WIDTH,
        "page-height": A4_HEIGHT,
        # enhancement
        "brightness":0,
        "contrast":0,
        "threshold":0,
        "rif":["yes","no"][1], # reverse-image-format
        # advanced
        # todo or not todo
        }

    return

if __name__ == "__main__":
    # todo: argparse devices.toml
    devices_toml = "/home/pi/pyScan/devices.toml"

    # todo: argparse scan_interval
    scan_interval = 1 # seconds

    # LIST OF DEVICES
    with open(devices_toml, "r") as devices_file:
        devices = tomlkit.load(devices_file)

    error = False

    while error is not True:

        try:
            avail = get_all_scanners()
            [process(scanner) for scanner in devices.values() if scanner['device'] in avail]
        except Exception as e:
            print("error")
            print(e)
            error = True

        error = True
        time.sleep(scan_interval)

    exit(0)
