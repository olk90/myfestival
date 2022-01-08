#!/usr/bin/env sh
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -U pip
pip install -r requirements.txt