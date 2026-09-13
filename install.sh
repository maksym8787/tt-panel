#!/bin/bash
set -euo pipefail

# Everything this script creates holds secrets (TLS key, VPN passwords, admin
# hash), so default to owner-only permissions rather than the root umask's 0644.
umask 077

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${GREEN}[+]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err()  { echo -e "${RED}[✗]${NC} $1"; exit 1; }
ask()  { echo -en "${CYAN}[?]${NC} $1: "; read -r REPLY; echo "$REPLY"; }

if [ "$(id -u)" -ne 0 ]; then err "Run as root"; fi

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   TrustTunnel + Admin Panel Installer    ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════╝${NC}"
echo ""

DOMAIN="${1:-}"
TIMEZONE="${2:-}"

if [ -z "$DOMAIN" ]; then
    echo -en "${CYAN}[?]${NC} Domain name (e.g. vpn.example.com): "
    read -r DOMAIN < /dev/tty || true
fi
if [ -z "$DOMAIN" ]; then err "Usage: bash install.sh <domain> [timezone]"; fi

if [ -z "$TIMEZONE" ]; then
    echo ""
    echo -e "  ${CYAN}Timezones:${NC}"
    echo -e "  1) Europe/Moscow"
    echo -e "  2) Europe/Kiev"
    echo -e "  3) Europe/Berlin"
    echo -e "  4) UTC"
    echo -e "  5) Other (enter manually)"
    echo -en "${CYAN}[?]${NC} Select timezone [1]: "
    read -r TZ_CHOICE < /dev/tty || true
    case "${TZ_CHOICE:-1}" in
        1) TIMEZONE="Europe/Moscow" ;;
        2) TIMEZONE="Europe/Kiev" ;;
        3) TIMEZONE="Europe/Berlin" ;;
        4) TIMEZONE="UTC" ;;
        5) echo -en "${CYAN}[?]${NC} Enter timezone (e.g. America/New_York): "
           read -r TIMEZONE < /dev/tty || true ;;
        *) TIMEZONE="Europe/Moscow" ;;
    esac
fi
if [ -z "$TIMEZONE" ]; then TIMEZONE="Europe/Moscow"; fi

TT_VERSION="${TT_VERSION:-1.1.0}"
# AdGuard release signing key (see VERIFY_RELEASES.md in the TrustTunnel repo).
TT_GPG_KEY="${TT_GPG_KEY:-28645AC9776EC4C00BCE2AFC0FE641E7235E2EC6}"
TT_DIR="/opt/trusttunnel"
PANEL_DIR="/opt/trusttunnel-panel"
PANEL_REPO="https://github.com/maksym8787/tt-panel.git"

log "Setting timezone to $TIMEZONE..."
timedatectl set-timezone "$TIMEZONE"

log "Installing dependencies..."
export DEBIAN_FRONTEND=noninteractive
export NEEDRESTART_SUSPEND=1
apt update
apt install -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" python3 python3-venv python3-pip certbot git curl openssl

log "Creating directories..."
mkdir -p "$TT_DIR/certs" "$PANEL_DIR"
chmod 700 "$TT_DIR/certs"
chmod 750 "$TT_DIR"
chmod 700 "$PANEL_DIR"

if [ ! -f "$TT_DIR/trusttunnel_endpoint" ]; then
    log "Downloading TrustTunnel endpoint v${TT_VERSION}..."
    TT_URL="https://github.com/TrustTunnel/TrustTunnel/releases/download/v${TT_VERSION}/trusttunnel-v${TT_VERSION}-linux-x86_64.tar.gz"
    if curl -fSL "$TT_URL" -o /tmp/tt-endpoint.tar.gz; then
        # The project publishes no sha256 file; the real chain of trust is the
        # AdGuard GPG signature shipped next to the binary inside the tarball.
        if [ -n "${TT_SHA256:-}" ]; then
            echo "${TT_SHA256}  /tmp/tt-endpoint.tar.gz" | sha256sum -c - \
                || err "Checksum mismatch for the TrustTunnel release — refusing to install"
            log "Checksum verified"
        fi

        TT_EXTRACT="$(mktemp -d)"
        tar -xzf /tmp/tt-endpoint.tar.gz -C "$TT_EXTRACT"
        rm -f /tmp/tt-endpoint.tar.gz

        TT_BIN_SRC="$(find "$TT_EXTRACT" -name trusttunnel_endpoint -type f | head -n1)"
        [ -z "$TT_BIN_SRC" ] && err "trusttunnel_endpoint not found inside the release archive"

        # Verify before the binary ever runs as root. Skip with TT_SKIP_GPG=1.
        if [ "${TT_SKIP_GPG:-0}" != "1" ] && [ -f "${TT_BIN_SRC}.sig" ]; then
            if command -v gpg >/dev/null 2>&1; then
                if ! gpg --list-keys "$TT_GPG_KEY" >/dev/null 2>&1; then
                    gpg --keyserver keys.openpgp.org --recv-key "$TT_GPG_KEY" >/dev/null 2>&1 \
                        || warn "Could not fetch the AdGuard signing key from the keyserver"
                fi
                if gpg --verify "${TT_BIN_SRC}.sig" "$TT_BIN_SRC" >/dev/null 2>&1; then
                    log "GPG signature verified (AdGuard)"
                else
                    rm -rf "$TT_EXTRACT"
                    err "GPG signature verification FAILED — refusing to install. Override with TT_SKIP_GPG=1 if you accept the risk."
                fi
            else
                warn "gpg not installed: the binary is unverified. apt install gnupg to enable verification."
            fi
        else
            warn "No signature found next to the binary — installing unverified."
        fi

        mv "$TT_BIN_SRC" "$TT_DIR/trusttunnel_endpoint"
        SW_SRC="$(find "$TT_EXTRACT" -name setup_wizard -type f | head -n1)"
        [ -n "$SW_SRC" ] && mv "$SW_SRC" "$TT_DIR/setup_wizard" && chmod +x "$TT_DIR/setup_wizard"
        rm -rf "$TT_EXTRACT"
    else
        warn "Download failed. Please manually place trusttunnel_endpoint binary at $TT_DIR/trusttunnel_endpoint"
        warn "Download from: https://github.com/TrustTunnel/TrustTunnel/releases"
        read -r -p "Press Enter when file is in place..." < /dev/tty || true
        [ ! -f "$TT_DIR/trusttunnel_endpoint" ] && err "Binary not found"
    fi
    chmod +x $TT_DIR/trusttunnel_endpoint
    log "TrustTunnel endpoint installed"
else
    log "TrustTunnel endpoint already exists, skipping download"
fi

install_certs() {
    cp "$1/fullchain.pem" "$TT_DIR/certs/cert.pem"
    cp "$1/privkey.pem" "$TT_DIR/certs/key.pem"
    # cp does not preserve mode; the private key must never be world-readable.
    chmod 644 "$TT_DIR/certs/cert.pem"
    chmod 600 "$TT_DIR/certs/key.pem"
}

CERT_OK=0
LE_DIR="/etc/letsencrypt/live/$DOMAIN"
if [ -f "$LE_DIR/fullchain.pem" ] && [ -f "$LE_DIR/privkey.pem" ]; then
    log "Existing certificate found, reusing"
    install_certs "$LE_DIR"
    CERT_OK=1
elif [ -f "$TT_DIR/certs/cert.pem" ] && [ -f "$TT_DIR/certs/key.pem" ]; then
    log "Certificates already in place, skipping"
    chmod 600 "$TT_DIR/certs/key.pem" 2>/dev/null || true
    CERT_OK=1
else
    log "Obtaining SSL certificate for $DOMAIN..."
    systemctl stop trusttunnel 2>/dev/null || true
    CERTBOT_EMAIL_ARG="--register-unsafely-without-email"
    if [ -n "${LE_EMAIL:-}" ]; then
        CERTBOT_EMAIL_ARG="--email ${LE_EMAIL}"
    fi
    if certbot certonly --standalone -d "$DOMAIN" --non-interactive --agree-tos $CERTBOT_EMAIL_ARG; then
        install_certs "$LE_DIR"
        log "Certificate installed"
        CERT_OK=1
    else
        warn "Certbot failed. Add certificates manually, then restart tt-admin:"
        warn "  cp /path/to/cert.pem $TT_DIR/certs/cert.pem"
        warn "  install -m 600 /path/to/key.pem $TT_DIR/certs/key.pem"
        warn "Until then the panel listens on 127.0.0.1 only (it refuses to serve"
        warn "a cleartext login publicly). Set LE_EMAIL=you@example.com to get"
        warn "Let's Encrypt expiry notifications on the next run."
    fi
fi
if [ "$CERT_OK" = "1" ]; then log "Certificate ready"; fi

log "Writing TrustTunnel configuration..."
cat > $TT_DIR/vpn.toml << TOMLEOF
listen_address = "0.0.0.0:443"
credentials_file = "credentials.toml"
rules_file = "rules.toml"
ipv6_available = true
allow_private_network_connections = false
tls_handshake_timeout_secs = 10
client_listener_timeout_secs = 600
connection_establishment_timeout_secs = 30
tcp_connections_timeout_secs = 604800
udp_connections_timeout_secs = 300
speedtest_enable = false
speedtest_path = "/speedtest"
ping_enable = false
ping_path = "/ping"
auth_failure_status_code = 407

[forward_protocol]
[forward_protocol.direct]

[listen_protocols]

[listen_protocols.http1]
upload_buffer_size = 32768

[listen_protocols.http2]
initial_connection_window_size = 8388608
initial_stream_window_size = 4194304
max_concurrent_streams = 1000
max_frame_size = 16384
header_table_size = 65536

[listen_protocols.quic]
recv_udp_payload_size = 1350
send_udp_payload_size = 1350
initial_max_data = 104857600
initial_max_stream_data_bidi_local = 1048576
initial_max_stream_data_bidi_remote = 1048576
initial_max_stream_data_uni = 1048576
initial_max_streams_bidi = 4096
initial_max_streams_uni = 4096
max_connection_window = 25165824
max_stream_window = 16777216
disable_active_migration = true
enable_early_data = true
message_queue_capacity = 4096

[icmp]
interface_name = "eth0"
request_timeout_secs = 3
recv_message_queue_capacity = 256

[metrics]
address = "127.0.0.1:1987"
request_timeout_secs = 3
TOMLEOF

cat > $TT_DIR/hosts.toml << TOMLEOF
ping_hosts = []
speedtest_hosts = []
reverse_proxy_hosts = []

[[main_hosts]]
hostname = "$DOMAIN"
cert_chain_path = "certs/cert.pem"
private_key_path = "certs/key.pem"
allowed_sni = []
TOMLEOF

cat > $TT_DIR/rules.toml << 'TOMLEOF'
TOMLEOF

if [ ! -f "$TT_DIR/credentials.toml" ]; then
    : > "$TT_DIR/credentials.toml"
fi
# Holds every VPN password in cleartext.
chmod 600 "$TT_DIR/credentials.toml"
chmod 644 "$TT_DIR/vpn.toml" "$TT_DIR/hosts.toml" "$TT_DIR/rules.toml"

# The panel's connection log / top-destinations come from lines the endpoint
# emits at DEBUG only ("Successfully connected to ...", "Tunnel closed
# gracefully"). Lowering this to info silently empties those views, so debug is
# the default. Set TT_LOG_LEVEL=info to stop recording destinations and user
# agents — accepting that the Monitor tab's connection log goes empty.
# The endpoint accepts only: info | debug | trace.
TT_LOG_LEVEL="${TT_LOG_LEVEL:-debug}"
case "$TT_LOG_LEVEL" in
    info|debug|trace) ;;
    *) err "TT_LOG_LEVEL must be one of: info, debug, trace (got '$TT_LOG_LEVEL')" ;;
esac

log "Creating TrustTunnel systemd service (log level: $TT_LOG_LEVEL)..."
cat > /etc/systemd/system/trusttunnel.service << EOF
[Unit]
Description=TrustTunnel endpoint
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$TT_DIR
ExecStart=$TT_DIR/trusttunnel_endpoint vpn.toml hosts.toml -l $TT_LOG_LEVEL
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=3
LimitNOFILE=65535

# Hardening: the endpoint is internet-facing, so limit what a compromise reaches.
NoNewPrivileges=true
ProtectSystem=strict
ReadWritePaths=$TT_DIR /var/log
ProtectHome=true
PrivateTmp=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictSUIDSGID=true
RestrictNamespaces=true
RestrictRealtime=true
LockPersonality=true
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX AF_NETLINK
CapabilityBoundingSet=CAP_NET_BIND_SERVICE CAP_NET_ADMIN CAP_NET_RAW
AmbientCapabilities=CAP_NET_BIND_SERVICE CAP_NET_ADMIN CAP_NET_RAW

[Install]
WantedBy=multi-user.target
EOF

log "Installing Admin Panel..."
cd /tmp
rm -rf tt-panel-install
# PANEL_REF pins a tag/commit; without it the default branch is deployed as-is.
PANEL_REF="${PANEL_REF:-}"
if [ -n "$PANEL_REF" ]; then
    git clone --depth 1 --branch "$PANEL_REF" "$PANEL_REPO" tt-panel-install || err "Failed to clone panel repo at $PANEL_REF"
else
    git clone --depth 1 "$PANEL_REPO" tt-panel-install || err "Failed to clone panel repo"
fi

cp tt-panel-install/auth.py $PANEL_DIR/
cp tt-panel-install/collector.py $PANEL_DIR/
cp tt-panel-install/config.py $PANEL_DIR/
cp tt-panel-install/database.py $PANEL_DIR/
cp tt-panel-install/main.py $PANEL_DIR/
cp tt-panel-install/network.py $PANEL_DIR/
cp -r tt-panel-install/frontend $PANEL_DIR/
cp -r tt-panel-install/routes $PANEL_DIR/
cp -r tt-panel-install/services $PANEL_DIR/
cp -r tt-panel-install/static $PANEL_DIR/
rm -rf /tmp/tt-panel-install

if [ ! -d "$PANEL_DIR/venv" ]; then
    log "Creating Python venv..."
    python3 -m venv $PANEL_DIR/venv
fi
$PANEL_DIR/venv/bin/pip install fastapi uvicorn

log "Creating panel systemd service..."
cat > /etc/systemd/system/tt-admin.service << EOF
[Unit]
Description=TrustTunnel Admin Panel
After=network-online.target trusttunnel.service
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$PANEL_DIR
ExecStart=$PANEL_DIR/venv/bin/python3 main.py
Restart=always
RestartSec=3
Environment=PYTHONUNBUFFERED=1
# Uncomment when running behind a TLS-terminating reverse proxy:
# Environment=TT_BEHIND_PROXY=1
# Disable third-party geolocation of client IPs:
# Environment=TT_GEO_LOOKUP=0

# Hardening. The panel still needs systemctl/certbot, so it stays root, but the
# filesystem and kernel surface are cut down.
ProtectHome=true
ProtectSystem=full
ReadWritePaths=$PANEL_DIR $TT_DIR /etc/letsencrypt /etc/systemd/system /etc/systemd/journald.conf.d /var/log
PrivateTmp=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictSUIDSGID=true
RestrictRealtime=true
LockPersonality=true
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX AF_NETLINK

[Install]
WantedBy=multi-user.target
EOF

log "Creating deploy script..."
cat > $PANEL_DIR/deploy.sh << 'DEPLOYEOF'
#!/bin/bash
set -euo pipefail
umask 077
cd /tmp
rm -rf tt-panel-deploy
# Fail loudly: silently continuing used to copy from a directory that never existed.
git clone --depth 1 https://github.com/maksym8787/tt-panel.git tt-panel-deploy \
    || { echo "Clone failed, keeping the current deployment" >&2; exit 1; }
cp tt-panel-deploy/auth.py /opt/trusttunnel-panel/
cp tt-panel-deploy/collector.py /opt/trusttunnel-panel/
cp tt-panel-deploy/config.py /opt/trusttunnel-panel/
cp tt-panel-deploy/database.py /opt/trusttunnel-panel/
cp tt-panel-deploy/main.py /opt/trusttunnel-panel/
cp tt-panel-deploy/network.py /opt/trusttunnel-panel/
cp -r tt-panel-deploy/frontend /opt/trusttunnel-panel/
cp -r tt-panel-deploy/routes /opt/trusttunnel-panel/
cp -r tt-panel-deploy/services /opt/trusttunnel-panel/
cp -r tt-panel-deploy/static /opt/trusttunnel-panel/
rm -rf /opt/trusttunnel-panel/__pycache__ /opt/trusttunnel-panel/frontend/__pycache__ /opt/trusttunnel-panel/routes/__pycache__ /opt/trusttunnel-panel/services/__pycache__
rm -rf /tmp/tt-panel-deploy
# panel.json holds the admin hash and VPN passwords; keep it owner-only.
chmod 700 /opt/trusttunnel-panel
chmod 600 /opt/trusttunnel-panel/panel.json 2>/dev/null || true
systemctl restart tt-admin
echo "Deployed at $(date)"
DEPLOYEOF
chmod +x $PANEL_DIR/deploy.sh

log "Configuring log rotation..."
mkdir -p /etc/systemd/journald.conf.d
cat > /etc/systemd/journald.conf.d/size.conf << 'EOF'
[Journal]
SystemMaxUse=50M
SystemKeepFree=500M
EOF

cat > /etc/logrotate.d/trusttunnel << 'EOF'
/var/log/trusttunnel.log {
    daily
    rotate 2
    maxsize 20M
    compress
    missingok
    notifempty
    copytruncate
}
EOF

cat > /etc/logrotate.d/syslog-custom << 'EOF'
/var/log/syslog {
    daily
    rotate 2
    maxsize 20M
    compress
    missingok
    notifempty
    postrotate
        /usr/lib/rsyslog/rsyslog-rotate
    endscript
}
EOF

log "Enabling and starting services..."
systemctl daemon-reload
systemctl enable trusttunnel tt-admin
systemctl restart systemd-journald
systemctl start tt-admin

log "Waiting for panel to start..."
PANEL_URL="https://127.0.0.1:8443"
if [ "$CERT_OK" != "1" ]; then PANEL_URL="http://127.0.0.1:8443"; fi
for i in $(seq 1 30); do
    if curl -sk "${PANEL_URL}/api/auth-status" >/dev/null 2>&1; then
        break
    fi
    sleep 2
done

echo ""
echo -e "${GREEN}════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Installation complete!${NC}"
echo -e "${GREEN}════════════════════════════════════════════${NC}"
echo ""
echo -e "  Domain:     ${CYAN}$DOMAIN${NC}"
echo -e "  Panel:      ${CYAN}https://$DOMAIN:8443${NC}"
echo -e "  TT Status:  $(systemctl is-active trusttunnel 2>/dev/null)"
echo -e "  Panel:      $(systemctl is-active tt-admin 2>/dev/null)"
echo ""
echo -e "  ${YELLOW}1. Open the panel and create admin password (min 12 chars)${NC}"
echo -e "  ${YELLOW}2. Add a VPN user through the panel${NC}"
echo -e "  ${YELLOW}3. TrustTunnel will start automatically${NC}"
echo ""
if [ "$CERT_OK" != "1" ]; then
    warn "No TLS certificate: the panel is bound to 127.0.0.1 only."
    warn "Reach it with: ssh -L 8443:127.0.0.1:8443 root@$DOMAIN"
fi
echo -e "  ${YELLOW}Recommended: restrict port 8443 to your own IP, e.g.${NC}"
echo -e "    ${CYAN}ufw allow from <your-ip> to any port 8443 proto tcp${NC}"
echo -e "    ${CYAN}ufw allow 443/tcp && ufw enable${NC}"
echo ""
echo -e "  Deploy updates:  ${CYAN}$PANEL_DIR/deploy.sh${NC}"
echo ""
