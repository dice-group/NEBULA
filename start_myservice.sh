#!/bin/bash
cd /data/nela/NEBULA
source virtual_env/bin/activate
cd org/diceresearch/nebula/
screen -dmS myservice python main.py
