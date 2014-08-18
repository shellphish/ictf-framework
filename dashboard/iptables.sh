#!/bin/bash
iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to 4567
