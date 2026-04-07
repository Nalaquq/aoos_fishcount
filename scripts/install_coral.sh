#!/usr/bin/env bash
# Install Google Coral Edge TPU runtime on Raspberry Pi.
# Run as: bash scripts/install_coral.sh

set -euo pipefail

echo "Installing Google Coral Edge TPU runtime..."

echo "deb https://packages.cloud.google.com/apt coral-edgetpu-stable main" \
  | sudo tee /etc/apt/sources.list.d/coral-edgetpu.list

curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg \
  | sudo apt-key add -

sudo apt-get update
sudo apt-get install -y libedgetpu1-std python3-pycoral

echo ""
echo "Coral runtime installed. Plug in the USB accelerator and verify:"
echo "  python3 -c \"from pycoral.utils import edgetpu; print(edgetpu.list_edge_tpus())\""
