#!/bin/bash
# Use bash strict mode
set -euo pipefail

# Delete the venv, if it already exists
rm -rf pyvenv

# Create the venv
python3 -m venv pyvenv

# Activate it
source pyvenv/bin/activate

# Upgrade pip inside the venv
pip install -U pip

# Install dependencies using uv
pip install uv
uv sync