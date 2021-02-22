#!/bin/python3
import io
from time import time
import docker
import os
import pathlib
import logging
import sys
import argparse
import subprocess
import tarfile
from typing import Dict, List

# Default values

DEFAULT_IMAGE = "lutris-vulkan"
VOLUME_NAME = "winehome"
SHM_SIZE = "4g"
PULSE_SOCKET = "/tmp/pulse-socket"
X_SOCKET_DIR = "/tmp/.X11-unix"
LUTRIS_RELATIVE_PATH = "lutris/bin/lutris"


class ContainerRuntime:
    def __init__(self, image: str, pulse_path: str, x_path: str, entrypoint: str = ""):
        self.logger = logging.getLogger("config")
        try:
            self.client = docker.from_env(version="auto")
        except docker.errors.DockerException:
            self.logger.error("Failed to connect Docker Daemon. Is it running with proper permissions?")
            sys.exit(1)
        self.envs: Dict = {}
        self.volumes: Dict = {}
        self.devices: List = []
        self.pulse_path = pathlib.Path(pulse_path)
        self.x_path = pathlib.Path(x_path)
        self.main_volume = "/home/wineuser"
        self.define_volumes()
        self.pass_devices()
        self.get_environment()
        try:
            self.image = self.client.images.get(image)
        except docker.errors.NotFound:
            self.logger.error("Image pull not implemented yet.")
            sys.exit(1)
        # Container starts Lutris on debug mode
        self.container = self.client.containers.create(image=self.image, auto_remove=True,
                                                       command=[f"{self.main_volume}/{LUTRIS_RELATIVE_PATH}", "-d"],
                                                       devices=self.devices,
                                                       environment=self.envs, shm_size=SHM_SIZE,
                                                       volumes=self.volumes)
        self.set_x_auth_token()
        self.socket = self.container.attach_socket(
            params={"logs": False, "stream": True, "stdout": True, "stderr": True, "stdin": False})

    def define_volumes(self):
        # --volume="${USER_VOLUME}:${USER_HOME}"
        # Pulseaudio server socket
        if self.pulse_path.is_socket():
            self.volumes[str(self.pulse_path)] = {"bind": str(self.pulse_path), "mode": "ro"}
            self.logger.debug(f"Pulseaudio found from in the path: {self.pulse_path}")
        else:
            self.logger.warning(f"Socket for Pulseaudio from the path '{self.pulse_path}'"
                                " not found. Sounds will not work.")
        # Xorg directory, read-only
        if self.x_path.is_dir():
            self.volumes[str(self.x_path)] = {"bind": str(self.x_path), "mode": "ro"}
            self.logger.debug(f"X server found in the path: {self.x_path}")
        else:
            self.logger.error(f"X server not found from the path '{self.x_path}'. Exiting...")
            sys.exit(1)

        # Volume for wine prefix or home directory
        try:
            volume = self.client.volumes.get(VOLUME_NAME)
            self.volumes[volume.id] = {"bind": self.main_volume, "mode": "rw"}
        except docker.errors.NotFound:
            self.logger.debug(f"No existing volume found with name {VOLUME_NAME}")
            self.logger.error("Creation not implemented yet..exiting..")
            sys.exit(1)

        self.logger.info("Following volume(s) exposed from the host:")
        for key in self.volumes.keys():
            self.logger.info(key)

    def get_environment(self):
        # Display value for Xorg
        self.envs["DISPLAY"] = os.environ.get("DISPLAY")

    def pass_devices(self):
        # GPUs via direct rendering
        # Tested only on integrated Intel
        gpu_path = pathlib.Path("/dev/dri")
        if gpu_path.is_dir():
            self.devices.append(f"{str(gpu_path)}:{str(gpu_path)}")
            self.logger.debug(f"GPUs found from the path: {gpu_path}")
        else:
            self.logger.warning(f"DRI path not found from: {gpu_path}. GPUs might not be accessible.")
        # sound cards
        snd_path = pathlib.Path("/dev/snd")
        if snd_path.is_dir():
            self.devices.append(f"{str(snd_path)}:{str(snd_path)}")
            self.logger.debug(f"Sound cards found in path: {snd_path}")
        else:
            self.logger.warning(f"No sound card devices found from the path {snd_path}")

    def set_x_auth_token(self):
        # Use xauth to get x-authority token to grant display access for container
        output = subprocess.run(["xauth", "list"], capture_output=True)
        if not output.stderr:
            buf = io.StringIO(output.stdout.decode("utf-8"))
            first_line = buf.readline()
            key = first_line.split()[-1]
            # Convert to bytes... again
            key = key.encode("utf-8")
            # Copy data into container to avoid volume usage
            tar_stream = io.BytesIO()
            tar_file = tarfile.TarFile(fileobj=tar_stream, mode="w")
            tar_info = tarfile.TarInfo(name='.Xkey')
            tar_info.size = len(key)
            tar_info.mtime = time()
            tar_info.mode = 0o0600
            tar_file.addfile(tar_info, io.BytesIO(key))
            tar_file.close()
            tar_stream.seek(0)
            resp = self.container.put_archive("/root/", tar_stream)
            if not resp:
                self.logger.error("Failed to upload xauth information into container. Display won't work.")
            else:
                self.logger.info(f"Xauthority token copied into container to grant display access.")
        else:
            self.logger.error(
                "You must have 'xauth' command line command available and to return"
                " Xauthority information to make display to work.")


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-l", "--log", dest="log_level", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help="Set the logging level", default="INFO")
    parser.add_argument("-d", "--detach", action="store_true",
                        help="Run detached.")
    parser.add_argument("--pulse", help="Set path for PulseAudio socket.", default=PULSE_SOCKET)
    parser.add_argument("--xorg", help="Set path for X socket directory.", default=X_SOCKET_DIR)
    args = parser.parse_args(args=sys.argv[1:])
    log_level = args.log_level if args.log_level else 'INFO'
    if log_level not in {'DEBUG'}:
        sys.tracebacklimit = 0  # track traces only when debugging
    logging.basicConfig(format='%(name)s: %(message)s', level=getattr(logging, log_level))
    logger = logging.getLogger("main")
    runtime = ContainerRuntime(DEFAULT_IMAGE, args.pulse, args.xorg)
    try:
        logger.info(f"Starting Lutris in container with id {runtime.container.short_id}")
        runtime.container.start()
        if not args.detach:
            for data in runtime.socket:
                # No use for header yet
                # header = data[:8]
                body = data[8:]
                print(body.decode("utf-8"), end="")
                # print("NEWLINE")
        else:
            logger.info("Leaving and not printing Lutris logs in detached mode.")
    finally:
        if not args.detach:
            logger.info("Killing container...")
            try:
                runtime.container.kill()
            except docker.errors.APIError:
                logger.debug("Could not kill container...not running anymore.")


def parse_data():
    pass


if __name__ == '__main__':
    main()
