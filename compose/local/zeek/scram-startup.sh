#!/bin/bash

# Check if UUID is blank or not a valid UUID format in config
CURRENT_UUID=$(grep "SCRAM_UUID=" /etc/sysconfig/scram-client.conf | cut -d'=' -f2)
UUID_PATTERN="^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"

if [ -z "$CURRENT_UUID" ] || ! echo "$CURRENT_UUID" | grep -Eq "$UUID_PATTERN"; then
    echo "No valid UUID found (current: '$CURRENT_UUID'), registering new client..."

    # register the client and hang on to that.
    REGISTER_OUTPUT=$(/home/zeek/scram_client_venv/bin/scram-client register django:8000 2>&1)

    if echo "$REGISTER_OUTPUT" | grep -q "Successfully registered"; then
        NEW_UUID=$(echo "$REGISTER_OUTPUT" | grep "New UUID:" | awk '{print $3}')
        echo "Registration successful, updating config with UUID: $NEW_UUID"

        # update the config file with the new UUID (but only if we changed it)
        sed "s/SCRAM_UUID=.*/SCRAM_UUID=$NEW_UUID/" /etc/sysconfig/scram-client.conf > /tmp/scram-client.conf.new
        cat /tmp/scram-client.conf.new > /etc/sysconfig/scram-client.conf
        rm /tmp/scram-client.conf.new
        echo "Config file updated successfully"
    else
        echo "Registration failed: $REGISTER_OUTPUT"
    fi
else
    echo "Valid UUID found: $CURRENT_UUID, skipping registration"
fi
