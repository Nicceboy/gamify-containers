FROM debian:buster as remote-conf
ENV DEBIAN_FRONTEND="noninteractive"
ARG WINE_BRANCH="stable"

RUN dpkg --add-architecture i386 \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        dbus-x11 \
        pulseaudio \
        x11-xserver-utils \
        apt-transport-https \
        ca-certificates \
        git \
        gosu \
        gpg-agent \
        p7zip \
        software-properties-common \
        tzdata \
        unzip \
        wget \
        zenity \
        gnupg \
        less \
        pciutils \
        stterm \
        htop \
        vim \
        vulkan-utils \
        mesa-vulkan-drivers \
        mesa-vulkan-drivers:i386 \
        libvulkan1 \
        libvulkan1:i386 \
        libglx-mesa0 \
        libgl1-mesa-dri \
        xauth \
        jq \
        curl \
        libcanberra-gtk-module \
        libcanberra-gtk3-module \
        # Install wine
        && curl -s https://dl.winehq.org/wine-builds/winehq.key | APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=1 apt-key add - \
        && apt-add-repository https://dl.winehq.org/wine-builds/debian/ \
        && curl -s https://download.opensuse.org/repositories/Emulators:/Wine:/Debian/Debian_10/Release.key | apt-key add -  \
        && echo "deb http://download.opensuse.org/repositories/Emulators:/Wine:/Debian/Debian_10 ./" | tee /etc/apt/sources.list.d/wine-obs.list \
        && apt-get update \
        && apt-get install -y --install-recommends winehq-${WINE_BRANCH} \
        && rm -rf /var/lib/apt/lists/*

# winetricks
RUN curl -Lo /usr/bin/winetricks https://raw.githubusercontent.com/Winetricks/winetricks/master/src/winetricks \
    && chmod +x /usr/bin/winetricks

# Lutris dependencies
RUN echo "deb http://download.opensuse.org/repositories/home:/strycore/Debian_10/ ./" | tee /etc/apt/sources.list.d/lutris.list \
    && wget -q https://download.opensuse.org/repositories/home:/strycore/Debian_10/Release.key -O- | apt-key add - \
    && apt-get update \
    && apt-get -y install \
    lutris \
    && rm -rf /var/lib/apt/lists/*

# Get latest Lutris client
RUN mkdir -p /tmp/lutris && \
    curl -s https://api.github.com/repos/lutris/lutris/releases/latest > /tmp/lutris/version.json && \
    jq ".tarball_url" /tmp/lutris/version.json | xargs curl -Lo /tmp/lutris/lutris && \
    mkdir -p /opt/lutris && \
    tar -C /opt/lutris --strip-components 1 -xf /tmp/lutris/lutris && \
    rm -rf /tmp/lutris

# Adduser
ENV USER_UID=1111
ENV USER_GID=${USER_UID}
ENV USER_NAME="lutris"
ENV USER_HOME="/home/${USER_NAME}"
ENV PULSE_GROUP="pulseaudio"

RUN groupadd --gid "${USER_GID}" "${USER_NAME}" && \
    useradd --shell /bin/bash --uid "${USER_UID}" --gid "${USER_GID}" \
      --no-create-home --home-dir "${USER_HOME}" "${USER_NAME}"

# Create group for pulseaudio and add user into it to limit permissions a bit
RUN groupadd "${PULSE_GROUP}" && usermod -a -G  "${PULSE_GROUP}" "${USER_NAME}"



# Disable some dbus warnings
ENV NO_AT_BRIDGE 1
COPY pulse-client.conf /root/pulse/client.conf
COPY entrypoint.sh /usr/bin/entrypoint
ENTRYPOINT ["/usr/bin/entrypoint"]
