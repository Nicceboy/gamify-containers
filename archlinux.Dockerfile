FROM archlinux:latest

ENV GOSU_VERSION=1.13

# We need all locales for Steam https://github.com/ValveSoftware/steam-for-linux/issues/5738
RUN sed -i '/^NoExtract/d' /etc/pacman.conf && \
    pacman-key --init && pacman -Sy && \
    pacman -Qqn | pacman -S --noconfirm - && \
    sed -i '$ a\[multilib]\nInclude = \/etc\/pacman.d\/mirrorlist' /etc/pacman.conf && \
    pacman -Syu --noconfirm && \
    pacman -S --noconfirm \
    jq \
    pulseaudio \
    git \
    vim \
    vulkan-tools \
    mesa \
    lib32-mesa \
    libva-mesa-driver \
    lib32-libva-mesa-driver \
    mesa-vdpau \
    lib32-mesa-vdpau \
    amdvlk \
    lib32-amdvlk \
    xorg-xauth \
    xorg-xrandr \
    xorg-apps \
    gtk3 \
    dbus-python \
    python3 \
    python-gobject \
    python-distro \
    python-evdev \
    python-gobject \
    python-lxml \
    python-pillow \
    python-requests \
    python-yaml \
    python-magic \
    gnome-desktop \
    webkit2gtk \
    zenity \ 
    lib32-libpulse \
    wine \
    samba \
    unzip \
    # glxinfo util
    mesa-demos \ 
    # Required for some MS dependecy installing
    cabextract \ 
    # Steam-only dependencies
    diffutils \
    # Steam requires namespaces, bwrap can do it without all capabilities
    bubblewrap-suid \
    steam \
    # gstreamer
    gst-plugins-good \
    lib32-gst-plugins-base \
    lib32-gst-plugins-good \
    # Steam runtime deps
    lib32-gtk2 \
    lib32-pipewire \
    lib32-libva \
    lib32-libvdpau \
    p7zip && \
    # Install gosu https://github.com/tianon/gosu
    curl -o /usr/bin/gosu -L "https://github.com/tianon/gosu/releases/download/${GOSU_VERSION}/gosu-amd64" && \
    chmod +x /usr/bin/gosu


# winetricks
RUN curl -Lo /usr/bin/winetricks https://raw.githubusercontent.com/Winetricks/winetricks/master/src/winetricks \
    && chmod +x /usr/bin/winetricks

# Get latest Lutris client
RUN mkdir -p /tmp/lutris && \
    curl -s https://api.github.com/repos/lutris/lutris/releases/latest > /tmp/lutris/version.json && \
    jq ".tarball_url" /tmp/lutris/version.json | xargs curl -Lo /tmp/lutris/lutris && \
    mkdir -p /opt/lutris && \
    tar -C /opt/lutris --strip-components 1 -xf /tmp/lutris/lutris && \
    rm -rf /tmp/lutris

# Adduser
ENV USER_UID=1000
ENV USER_GID=${USER_UID}
ENV USER_NAME="lutris"
ENV USER_HOME="/home/${USER_NAME}"
# Disable Steam runtime
ENV STEAM_RUNTIME=0
ENV STEAM_RUNTIME_HEAVY=0
# ENV LD_PRELOAD="/usr/lib64/libstdc++.so.6 /usr/lib32/libstdc++.so.6"

# Additionally, might need to add manually
# shift 4
# exec "${@}"
# into the file <steam-library>/steamapps/common/SteamLinuxRuntime_soldier/_v2-entry-point
# https://github.com/flightlessmango/MangoHud/issues/369
#


# User needs audio group for raw ALSA to work
RUN groupadd --gid "${USER_GID}" "${USER_NAME}" && \
    useradd --shell /bin/bash --uid "${USER_UID}" --gid "${USER_GID}" \
      --no-create-home --home-dir "${USER_HOME}" "${USER_NAME}" && \
    mkdir -p /var/lib/dbus && \
    dbus-uuidgen > /var/lib/dbus/machine-id 

# Disable some dbus warnings
ENV NO_AT_BRIDGE 1

COPY pulse-client.conf /root/pulse/client.conf
COPY entrypoint.sh /usr/bin/entrypoint
ENTRYPOINT ["/usr/bin/entrypoint"]