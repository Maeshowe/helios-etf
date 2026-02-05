# HELIOS ETF FLOW - Linux Server Deployment

## Quick Start

```bash
# Clone repository
cd /home/safrtam
git clone https://github.com/Maeshowe/helios-etf.git
cd helios-etf

# Run deployment script
chmod +x scripts/deploy_linux.sh
./scripts/deploy_linux.sh

# Configure API keys
nano .env
```

## Systemd Setup

### 1. Install systemd files

```bash
# Daily pipeline
sudo cp scripts/helios-daily.service /etc/systemd/system/
sudo cp scripts/helios-daily.timer /etc/systemd/system/

# Dashboard web service (port 8504)
sudo cp scripts/helios-dashboard.service /etc/systemd/system/

sudo systemctl daemon-reload
```

### 2. Enable and start services

```bash
# Enable daily pipeline timer
sudo systemctl enable helios-daily.timer
sudo systemctl start helios-daily.timer

# Enable and start dashboard
sudo systemctl enable helios-dashboard
sudo systemctl start helios-dashboard
```

### 3. Verify

```bash
# Check timer status
sudo systemctl status helios-daily.timer
sudo systemctl list-timers --all | grep helios

# Check dashboard status
sudo systemctl status helios-dashboard

# Check logs
journalctl -u helios-daily.service -f
journalctl -u helios-dashboard.service -f
```

## Nginx Configuration (Multi-site)

Add to `/etc/nginx/sites-available/helios.ssh.services`:

```nginx
server {
    listen 80;
    server_name helios.ssh.services;

    location / {
        proxy_pass http://127.0.0.1:8504;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/helios.ssh.services /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# SSL with certbot
sudo certbot --nginx -d helios.ssh.services
```

## Port Allocation

| Service | Port | Domain |
|---------|------|--------|
| moneyflows | 8501 | https://moneyflows.ssh.services |
| obsidian | 8502 | https://obsidian.ssh.services |
| aurora | 8503 | https://aurora.ssh.services |
| helios | 8504 | https://helios.ssh.services |
| atlas | 8505 | https://atlas.ssh.services |

## Schedule

Daily pipeline runs **Mon-Fri at 21:00 UTC** (22:00 CET), after US market close.

## Manual Commands

```bash
cd /home/safrtam/helios-etf

# Run daily pipeline manually
uv run python scripts/run_daily.py

# Run for specific date
uv run python scripts/run_daily.py --date 2026-02-04

# Run with verbose logging
uv run python scripts/run_daily.py --force --verbose

# Check API health
uv run python scripts/diagnose_api.py

# Run dashboard manually (for testing)
uv run streamlit run helios/dashboard/app.py --server.port 8504
```

## Data Collection Timeline

| Day | Status |
|-----|--------|
| 1-21 | Collecting data, INSUFFICIENT status |
| 21+ | Rolling baselines active, full state classification |

## Troubleshooting

```bash
# Check logs
journalctl -u helios-daily.service --since today
journalctl -u helios-dashboard.service --since today

# Check API keys
cd /home/safrtam/helios-etf
uv run python scripts/diagnose_api.py

# Force run pipeline now
sudo systemctl start helios-daily.service

# Restart dashboard
sudo systemctl restart helios-dashboard
```

## Git Pull Updates

```bash
cd /home/safrtam/helios-etf
git pull origin main
uv sync
sudo systemctl restart helios-dashboard
```
