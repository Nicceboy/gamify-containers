# Gamifying containers - play your Windows games on Linux containers with Lutris and Wine

![build](https://img.shields.io/github/workflow/status/Nicceboy/gamify-containers/Docker) ![License](https://img.shields.io/github/license/Nicceboy/gamify-containers) 


This project essentially attempts to set suitable environment for running Windows games from Linux containers. Python script is used to run specifically made container. Docker has been used as container engine.

Game installation, running and other management is handled with [Lutris](https://lutris.net/) which attempts to automate a lot of painful stuff, such as managing suitable Wine versions, required dependencies for game to be functional and handling runner environments such as [dxvk](https://github.com/doitsujin/dxvk) for DirectX to Vulkan transitions for performance boost.

In practice, provided Python script opens the graphical user interface of the Lutris from the container while configuring display and sound redirections.

Game data, Wine prefix and Lutris environment is stored in volume which is named as `lutrishome`.
Runtime Linux is defined in Docker image. See Dockerfile for [reference.](Dockerfile)

## Why the hassle

  * Setting up your specific GPU drivers with Vulkan support, Wine and other mandatory software comes with a lot of dependencies, and you *might not always want* to get those in your host system
  * Isolated code execution, at least on some level. Exposed components are listed on [exposed components](#exposed-components-from-the-host) section.
  * Easier version upgrade on those packages
  * If you need some space, it is easy to just delete Docker image(s) but maintain the game data itself from volumes.

This has probably downside for performance, but sometimes it is not that meaningful.

## Usage

You can pull required Docker image with command:
```
docker pull ghcr.io/nicceboy/lutris-vulkan
```

Configure [sound.](#configuring-sound)

Code can be installed as package:
```
pip install git+https://github.com/Nicceboy/gamify-containers
```

Launch Lutris from container!

```
playlutris
```

## Prerequisites
  * Docker Engine
  * PulseAudio as audio server on host (PipeWire maybe some day)
  * Xorg display server (Wayland support maybe in future) on host
  * Python 3
  
On Debian based system, packages can be installed with
```
apt-get update && apt-get install pulseaudio docker.io python3
```

## Configuring sound

This step is not automated, user should be aware of the changes.

To be able to get sound from the container, Unix socket for PulseAudio must be created beforehand. This can be achieved by modifying configuration files and then restarting server.

Server access will enabled by copying user specific PulseAudio cookie into container. By default it is looked from the path  ~/.config/pulse/cookie`

Look for user-specific pulse configuration file in path:
```
cat "${HOME}/.config/pulse/default.pa"
```
Create/modify the file with following contents:
```ini
.include /etc/pulse/default.pa
load-module module-native-protocol-unix socket=/tmp/pulse-socket
```

Default socket path fill be at `/tmp/pulse-socket`. Then restart server.
```cmd
pulseaudio -k
pulseaudio --start
pulseaudio --check
```
Socket should be available. 
```cmd
$ file /tmp/pulse-socket
/tmp/pulse-socket: socket
```

## Display Server

At the moment, pure Wayland applications are not supported.
X applications are still usable with Wayland because it provides XWayland compositor. 

There is difference how XWayland and traditional X server behaves; XWayland seems to require same UID than server itself, when socket is accessed. Regular X does not. This has impact for user namespace on underlying container; same needs to be used and therefore less isolation is achieved.

To authenticate container for using X, Xauthority token is copied into container and X Unix socket is shared as volume in to container.

By default, path `/tmp/.X11-unix` will be used.

`xauth` command is expected to be found from the host machine.

## Graphic Cards

By default, graphic cards are passed as devices into container from the path `/dev/dri`. Provided image has AMD and Intel drivers installed, with 32 and 64-bit Vulkan support. NVIDIA drivers should be installed manually, if there is need for them.

## Exposed components from the host

Following paths are exposed with read-only binds from the host system into container.

 * Xorg server - `/tmp/.X11-unix`
 * PulseAudio socket - `/tmp/pulse-socket`
 
 Passed as devices
 * Graphic cards - `/dev/dri`
 
 ## Command line commands without using Python
 
 TODO
 
 ## License 
 
 MIT