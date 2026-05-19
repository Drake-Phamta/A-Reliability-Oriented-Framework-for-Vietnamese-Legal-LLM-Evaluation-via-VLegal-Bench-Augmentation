#!/bin/bash
set -e

python3 -m venv venv

python -m pip install --upgrade pip
pip install -r requirements.txt
