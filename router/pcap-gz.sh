#! /bin/bash
gzip -S ".tmp" "$1"
mv "$1.tmp" "$1.gz"
