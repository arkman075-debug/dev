#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Download and install ffmpeg (standard for Render's Linux environment)
# This is a bit advanced, but it works on Render's 'Web Service'