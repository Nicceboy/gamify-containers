#!/usr/bin/env bash
# Credits for https://github.com/scottyhardy/docker-wine for lot of tips
# Timezone
TZ=${TZ:-UTC}
ln -snf "/usr/share/zoneinfo/${TZ}" /etc/localtime && echo "${TZ}" > /etc/timezone
# Create home if it doesn't exist
# We have mounted this directory at this point
[ ! -d "${USER_HOME}" ] && mkdir -p "${USER_HOME}"
# Take ownership of user's home directory if owned by root
OWNER_IDS="$(stat -c "%u:%g" "${USER_HOME}")"
if [ "${OWNER_IDS}" != "${USER_UID}:${USER_GID}" ]; then
    if [ "${OWNER_IDS}" == "0:0" ]; then
        chown -R "${USER_UID}":"${USER_GID}" "${USER_HOME}"
    else
        echo "ERROR: User's home '${USER_HOME}' is currently owned by $(stat -c "%U:%G" "${USER_HOME}")"
        exit 1
    fi
fi
# Use host Unix socket for pulseaudio
if [ -e /tmp/pulse-socket ]; then
    [ -f /root/pulse/client.conf ] && cp /root/pulse/client.conf /etc/pulse/client.conf
fi
# Generate .Xauthority using xauth with .Xkey sourced from host
if [ -f /root/.Xkey ]; then
    [ ! -f /root/.Xauthority ] && touch /root/.Xauthority
    xauth add "$DISPLAY" . "$(cat /root/.Xkey)"
fi
# Copy and take ownership of .Xauthority
if [ -f /root/.Xauthority ]; then
    cp /root/.Xauthority "${USER_HOME}"
    chown "${USER_UID}":"${USER_GID}" "${USER_HOME}/.Xauthority"
fi
# Copy pulseaudio auth token
if [ -f /root/pulse_cookie ]; then
    cp /root/pulse_cookie "${USER_HOME}/.config/pulse/cookie"
    chown "${USER_UID}":"${USER_GID}" "${USER_HOME}/.config/pulse/cookie"
fi
# Switch to non-root user
exec gosu "${USER_NAME}" "$@"