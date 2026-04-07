# Software Installation

## Raspberry Pi OS Setup

1. Flash Raspberry Pi OS (64-bit Bookworm) using Raspberry Pi Imager
2. Pre-configure hostname (`salmon-rpi`), SSH, and user in Imager settings
3. Boot and connect via SSH

## Package Installation

```bash
# Update system
sudo apt update && sudo apt full-upgrade -y

# Enable I2C for BME280
sudo raspi-config  # Interface Options → I2C → Enable

# Clone repo
git clone https://github.com/Nalaquq/aoos_fishcount.git
cd aoos_fishcount

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install package
pip install -e ".[dev]"

# Install Coral runtime
bash scripts/install_coral.sh
```

## Tailscale (Remote Access)

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
# Follow the auth URL to link to your Tailscale account
```

## Verify Installation

```bash
python scripts/health_check.py
```

All checks should pass before field deployment.
