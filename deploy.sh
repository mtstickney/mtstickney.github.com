#!/bin/sh

OUTPUT_DIR=output
# Generate fresh production output
rm -rf "$OUTPUT_DIR"
pelican -s publishconf.py

# Just to be safe, make sure we don't commit staged changes
git reset HEAD

# Add and commit the new output
git add --all "$OUTPUT_DIR"
DATE=$(date -u "+%Y-%m-%d %H:%M:%S %Z")
git commit -m "Site updated at $DATE"

# push it to the master
git subtree push --prefix "$OUTPUT_DIR" origin master
