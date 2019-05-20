#!/usr/bin/env python
# encoding: utf-8
import subprocess

# Constants
VERSION = 'v0.01'
try:
    VERSION = str(subprocess.check_output(["git", "describe", "--tags"], stderr=subprocess.DEVNULL).rstrip())
except Exception as e:
    # git not available, ignore
    pass
