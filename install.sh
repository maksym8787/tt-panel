#!/bin/bash
set -e

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

DOMAIN=$(ask "Domain name (e.g. vpn.example.com)")
if [ -z "$DOMAIN" ]; then err "Domain required"; fi

TT_VERSION="1.0.27"
TT_DIR="/opt/trusttunnel"
PANEL_DIR="/opt/trusttunnel-panel"
PANEL_REPO="https://github.com/maksym8787/tt-panel.git"

log "Installing dependencies..."
apt update -qq
apt install -y -qq python3 python3-venv python3-pip certbot git curl openssl > /dev/null 2>&1

log "Creating directories..."
mkdir -p $TT_DIR/certs $PANEL_DIR

if [ ! -f "$TT_DIR/trusttunnel_endpoint" ]; then
    log "Downloading TrustTunnel endpoint v${TT_VERSION}..."
    TT_URL="https://github.com/nicholasgasior/trusttunnel/releases/download/v${TT_VERSION}/trusttunnel_endpoint-x86_64-unknown-linux-gnu"
    if ! curl -fsSL "$TT_URL" -o "$TT_DIR/trusttunnel_endpoint" 2>/dev/null; then
        warn "Auto-download failed. Trying alternative..."
        TT_URL="https://github.com/nicholasgasior/trusttunnel/releases/latest/download/trusttunnel_endpoint-x86_64-unknown-linux-gnu"
        if ! curl -fsSL "$TT_URL" -o "$TT_DIR/trusttunnel_endpoint" 2>/dev/null; then
            warn "Download failed. Please manually place trusttunnel_endpoint binary at $TT_DIR/trusttunnel_endpoint"
            warn "Download from: https://github.com/nicholasgasior/trusttunnel/releases"
            read -p "Press Enter when file is in place..."
            [ ! -f "$TT_DIR/trusttunnel_endpoint" ] && err "Binary not found"
        fi
    fi
    chmod +x $TT_DIR/trusttunnel_endpoint
    log "TrustTunnel endpoint installed"
else
    log "TrustTunnel endpoint already exists, skipping download"
fi

log "Obtaining SSL certificate for $DOMAIN..."
systemctl stop trusttunnel 2>/dev/null || true
certbot certonly --standalone -d "$DOMAIN" --non-interactive --agree-tos --register-unsafely-without-email --force-renewal || err "Certbot failed. Is port 80 open? Is $DOMAIN pointing to this server?"
LE_DIR="/etc/letsencrypt/live/$DOMAIN"
cp "$LE_DIR/fullchain.pem" "$TT_DIR/certs/cert.pem"
cp "$LE_DIR/privkey.pem" "$TT_DIR/certs/key.pem"
log "Certificate installed"

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

touch $TT_DIR/credentials.toml

log "Creating TrustTunnel systemd service..."
cat > /etc/systemd/system/trusttunnel.service << EOF
[Unit]
Description=TrustTunnel endpoint
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$TT_DIR
ExecStart=$TT_DIR/trusttunnel_endpoint vpn.toml hosts.toml -l debug
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=3
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF

log "Installing Admin Panel..."
cd /tmp
rm -rf tt-panel-install
git clone "$PANEL_REPO" tt-panel-install 2>/dev/null || err "Failed to clone panel repo"

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
$PANEL_DIR/venv/bin/pip install -q fastapi uvicorn 2>/dev/null

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

[Install]
WantedBy=multi-user.target
EOF

log "Creating deploy script..."
cat > $PANEL_DIR/deploy.sh << 'DEPLOYEOF'
#!/bin/bash
cd /tmp
rm -rf tt-panel-deploy
git clone https://github.com/maksym8787/tt-panel.git tt-panel-deploy 2>/dev/null
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
systemctl start trusttunnel
sleep 2
systemctl start tt-admin

log "Waiting for panel to start..."
for i in $(seq 1 30); do
    if curl -sk "https://127.0.0.1:8443/api/auth-status" >/dev/null 2>&1; then
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
echo -e "  ${YELLOW}Open the panel URL and create admin password${NC}"
echo -e "  ${YELLOW}Then add VPN users through the panel${NC}"
echo ""
echo -e "  Deploy updates:  ${CYAN}$PANEL_DIR/deploy.sh${NC}"
echo ""
