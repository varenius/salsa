#!/bin/bash

BIN_DIR=build

if [ "$1" == "VALE" ]; then
    ./$BIN_DIR/rio_server VALE 169.254.212.76 23
elif [ "$1" == "BRAGE" ]; then
    ./$BIN_DIR/rio_server BRAGE 192.168.1.152 23
else
    echo "Please specify target (VALE/BRAGE)"
fi
