#!/bin/bash

stop_chromium() {
    docker stop selenium-chromium
    docker rm selenium-chromium
    echo "Chromium stopped"
}

stop_chromium