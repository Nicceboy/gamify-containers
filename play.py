#!/bin/python3
import io
import docker
import os
import pathlib
import logging
import sys
import argparse
import subprocess
from typing import Dict, List

DEFAULT_IMAGE = "wine-remote"
VOLUME_NAME = "winehome"
SHM_SIZE = "4g"


class ContainerRuntime:
    def __init__(self, image: str, entrypoint: str = ""):
        self.logger = logging.getLogger("config")
        try:
            self.client = docker.from_env(version="auto")
        except docker.errors.DockerException:
            self.logger.error("Failed to connect Docker Daemon. Is it running with proper permissions?")
            sys.exit(1)
        self.envs: Dict = {}
        self.volumes: Dict = {}
        self.devices: List = []
        self.main_volume = "/home/wineuser"
        self.define_volumes()
        self.pass_devices()
        self.pass_environment()
        self.set_x_auth_token()
        try:
            self.image = self.client.images.get(image)
        except docker.errors.NotFound:
            self.logger.error("Image pull not implemented yet.")
            sys.exit(1)
        self.container = self.client.containers.create(image=self.image, auto_remove=True,
                                                       command=[f"{self.main_volume}/lutris/bin/lutris", "-d"],
                                                       devices=self.devices,
                                                       environment=self.envs, shm_size=SHM_SIZE,
                                                       volumes=self.volumes)
        self.socket = self.container.attach_socket(
            params={"logs": False, "stream": True, "stdout": True, "stderr": True, "stdin": False})

    def define_volumes(self):
        # --volume="${USER_VOLUME}:${USER_HOME}"
        # Pulseaudio server socket
        pulse_path = pathlib.Path("/tmp/pulse-socket")
        if pulse_path.is_socket():
            self.volumes[str(pulse_path)] = {"bind": str(pulse_path), "mode": "ro"}
            self.logger.debug(f"Pulseaudio found in path: {pulse_path}")
        else:
            self.logger.warning(f"Socket for Pulseaudio from the path '{pulse_path}' not found. Sounds will not work.")
        # Sound
        snd_path = pathlib.Path("/dev/snd")
        if snd_path.is_dir():
            self.volumes[str(snd_path)] = {"bind": str(snd_path), "mode": "ro"}
            self.logger.debug(f"Sound cards found in path: {snd_path}")
        else:
            self.logger.warning(f"No sound card devices found from the path {snd_path}")
        # Xorg socket, read-only
        x_path = pathlib.Path("/tmp/.X11-unix")
        if x_path.is_dir():
            self.volumes[str(x_path)] = {"bind": str(x_path), "mode": "ro"}
            self.logger.debug(f"X server found in the path: {x_path}")
        else:
            self.logger.error(f"X server not found from the path '{x_path}'. Exiting...")
            sys.exit(1)

        # Volume for wine prefix or home directory
        try:
            volume = self.client.volumes.get(VOLUME_NAME)
            self.volumes[volume.id] = {"bind": self.main_volume, "mode": "rw"}
        except docker.errors.NotFound:
            self.logger.debug(f"No existing volume found with name {VOLUME_NAME}")
            self.logger.error("Creation not implemented yet..exiting..")
            sys.exit(1)

        self.logger.info("Volumes defined. Following paths exposed in read-only:")
        for key in self.volumes.keys():
            self.logger.info(key)

    def pass_environment(self):
        # Display value for Xorg
        self.envs["DISPLAY"] = os.environ.get("DISPLAY")

    def pass_devices(self):
        # GPUs via direct rendering
        # Tested only on integrated Intel
        gpu_path = pathlib.Path("/dev/dri")
        if gpu_path.is_dir():
            self.devices.append("/dev/dri:/dev/dri")
            self.logger.debug(f"GPUs found from the path: {gpu_path}")

    def set_x_auth_token(self):
        # Use xauth to get x-authority token
        output = subprocess.run(["xauth", "list"], capture_output=True)
        if not output.stderr:
            buf = io.StringIO(output.stdout.decode("utf-8"))
            first_line = buf.readline()
            key = first_line.split()[-1]
        else:
            self.logger.error("You must have 'xauth' command line command available to make display to work.")

        xauth_token_path = pathlib.Path.home() / ".docker-lutris.Xkey"
        self.logger.info(f"Creating new Xauthority token to be shared for container in path {xauth_token_path}")
        with xauth_token_path.open("w") as f:
            f.write(key)
        # Read-only bind mount for Xkey
        self.volumes[xauth_token_path] = {"bind": "/root/.Xkey", "mode": "ro"}


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-l", "--log", dest="log_level", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help="Set the logging level", default=None)
    args = parser.parse_args(args=sys.argv[1:])
    # if len(sys.argv) > 1:
    #     args = parser.parse_args(args=sys.argv[1:])
    # else:
    #     args = parser.parse_args(args=['--help'])
    log_level = args.log_level if args.log_level else 'INFO'
    if log_level not in {'DEBUG'}:
        sys.tracebacklimit = 0  # track traces only when debugging
    logging.basicConfig(format='%(name)s: %(message)s', level=getattr(logging, log_level))

    config = ContainerRuntime(DEFAULT_IMAGE)
    config.container.start()
    for data in config.socket:
        # No use for header yet
        # header = data[:8]
        body = data[8:]
        print(body.decode("utf-8"), end="")
        # print("NEWLINE")


def parse_data():
    pass


if __name__ == '__main__':
    main()
