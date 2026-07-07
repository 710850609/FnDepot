#!/bin/bash

### This script is called after the user installs the application.
set -e

LOG_FILE="${TRIM_PKGVAR}/logs/cmd.log"
SCRIPT_PATH="${TRIM_APPDEST}/backend"


log_msg() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> ${LOG_FILE}
}

warm_exit() {
    log_msg "$1"
    echo "$1" > ${TRIM_TEMP_LOGFILE}
    exit 1
}

run_cmd() {
    log_msg "运行命令: $1"
    bash -c "$1" >> ${LOG_FILE} 2>&1
}