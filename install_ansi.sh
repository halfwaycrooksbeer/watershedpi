#!/bin/bash

# Download
curl -OL git.io/ansi

# Make executable
chmod 755 ansi

# Copy to somewhere in your path
sudo mv ansi /usr/local/bin/
