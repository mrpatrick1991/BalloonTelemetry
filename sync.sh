#!/bin/sh  
while true  
do  
  python BalloonTelemetry.py VE6AZX-14
  python BalloonTelemetry.py VE6AZX-15
  sleep 300 # wait 5 minutes between syncs
done
