#!/bin/bash

hexdump -v -e '"\\" "x" 1/1 "%02X"' "$1"
