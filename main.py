#! /usr/bin/env python

import tomlkit
import time

from utils import get_all_scanners, process

if __name__ == "__main__":
    # todo: argparse devices.toml
    devices_toml = "/home/pi/pyScan/devices.toml"

    # todo: argparse scan_interval
    scan_interval = 1 # seconds

    # LIST OF DEVICES
    with open(devices_toml, "r") as devices_file:
        devices = tomlkit.load(devices_file)
    print(devices)
    error = False

    while error is not True:

        try:
            avail = get_all_scanners()
            [process(scanner) for scanner in devices.values() if scanner['device'] in avail]
        except Exception as e:
            print("error")
            print(e)
            error = True

        error = False
        time.sleep(scan_interval)

    exit(0)
