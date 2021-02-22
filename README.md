# Gamifying containers - play your Windows games on Linux containers with Lutris and Wine

This project essentially attempts to set suitable environment for running Windows games from Linux containers. Python script is used to run specifically made container.

Game installation and management is handled with [Lutris](https://lutris.net/) which attempts to automate a lot of painful stuff, such as managing suitable Wine versions, required dependencies for game to be functional and handling runner environments such as [dxvk](https://github.com/doitsujin/dxvk) for DirectX to Vulkan transitions for performance boost.

## Why the hassle

  * Setting up your specific GPU drivers with Vulkan support, Wine and other mandatory software comes with a lot of dependencies, and you *might not always want* to get those in your host system
  * Isolated code execution, at least on some level. Exposed components are listed on [exposed volumes](#exposed_components_from_the_host) section.
  * Easier version upgrade on those packages
  * If you need some space, it is easy to just delete Docker image(s) but maintain the game data itself from volumes.

## Prerequisites
  * Docker Engine
  * PulseAudio as audio server on host (PipeWire maybe some day)
  * Xorg display server (Wayland support maybe in future) on host
  * Python 3
  
On Debian based system, packages can be installed with
```
apt-get update && apt-get install pulseaudio docker.io python3
```
If you don't have Xorg display server already, you might want to skip this project for now.

However, sometimes in the log-in phase for Linux distribution, you can select the environment, e.g. Gnome With Xorg if it is installed, but not used.

## Configuring sound

This step is not automated, user should be aware of the changes.

To be able to get sound from the container, Unix socket for PulseAudio must be created beforehand. This can be achieved by modifying configuration files and then restarting server.

Server will enabled to be accessed by other users.
Look for user-specific pulse configuration file in path:
```
cat "${HOME}/.config/pulse/default.pa"
```
Create/modify the file with following contents:
```ini
.include /etc/pulse/default.pa
load-module module-native-protocol-unix 
auth-anonymous=1 
socket=/tmp/pulse-socket
```

Then restart server
```cmd
pulseaudio -k
pulseaudio --start
pulseaudio --check
```
Socket should be available 
```cmd
file /tmp/pulse-socket
```


## Exposed components from the host

Following paths are exposed with read-only binds from the host system into container.

 * Xorg server - `/tmp/.X11-unix`
 * PulseAudio socket - `/tmp/pulse-socket`
 
 Passed as devices
 * Sound cards - `/dev/snd`
 * Graphic cards - `/dev/dri`