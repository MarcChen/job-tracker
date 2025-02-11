#!/usr/bin/env bash

set_env_vars() {
    env_file=".env"
    if [[ ! -f "$env_file" ]]; then
        echo "No .env file found in the current directory."
        return 1
    fi

    echo "Exporting variables from $env_file"
    while IFS= read -r line || [[ -n "$line" ]]; do
        # Ignore empty lines and comments
        if [[ -n "$line" && "$line" != \#* ]]; then
            # Remove any surrounding quotes from the variable value
            var_name=$(echo "$line" | cut -d '=' -f 1)
            var_value=$(echo "$line" | cut -d '=' -f 2- | sed -e 's/^"//' -e 's/"$//')
            # Export the variable as an environment variable
            export "$var_name=$var_value"
        fi
    done < "$env_file"
    echo "Variables exported from $env_file"
}

launch_chromium() {
    docker run -d --name selenium-chromium -p 4444:4444 -p 7900:7900 --shm-size="2g" selenium/standalone-chromium
    echo "Chromium launched"
    echo "Access the Selenium Grid console at http://localhost:7900/?autoconnect=1&resize=scale&password=secret"
    set_env_vars
    poetry shell
}

# Execute launch_chromium if the script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    launch_chromium
fi