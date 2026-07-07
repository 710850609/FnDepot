#!/bin/bash

chmod +x build.sh
./build.sh release=true arch=x86_64
./build.sh release=true arch=aarch64
#./build.sh release=true arch=riscv64

exit 0