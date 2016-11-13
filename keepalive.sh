#!/bin/sh

while true; do
  nohup python3 server.py >> test.out
done &
