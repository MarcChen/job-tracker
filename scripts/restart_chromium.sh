#!/bin/bash
restart_chromium() {
    docker stop selenium-chromium
    docker rm selenium-chromium
    DIR="$(dirname "$0")"
    bash "$DIR/launch_chromium.sh"
}
restart_chromium
