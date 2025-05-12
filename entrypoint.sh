#!/bin/bash

# install rapida tool and dependencies
pipenv run pip install git+https://github.com/UNDP-Data/rapida

# Create multiple users from environment variable SSH_USERS
# Format: JUPYTER_USERS="user1:password1 user2:password2 user3:password3"


if [ ! -z "$JUPYTER_USERS" ]; then
     # Create a group and set permissions for /app
#    mkdir -p /data/notebooks


    groupadd ${GROUP_NAME} && \
         usermod -aG ${GROUP_NAME} root && \
         mkdir -p /app && \
         chown -R :${GROUP_NAME} /app && \
         chmod -R g+rwx /app && \
         mkdir -p $DATA_DIR && \
         chown -R :${GROUP_NAME} $DATA_DIR

    cp -r /app/notebooks ${DATA_DIR}/notebooks

    # Set permissions so that users in GROUP_NAME can write to /data/notebooks
    chown -R :${GROUP_NAME} ${DATA_DIR}/notebooks
    chmod -R g+rwX ${DATA_DIR}/notebooks


    for user_info in $JUPYTER_USERS; do
        IFS=':' read -r username password <<< "$user_info"
        if [ ! -z "$username" ] && [ ! -z "$password" ]; then
            /app/create_user.sh "$username" "$password"

            echo "Creating Jupyter user $username profile directories..."

            # Ensure the home directory exists first
            if [ ! -d "/home/$username" ]; then
                echo "Home directory for $username does not exist. Creating..."
                mkdir -p /home/$username
                chown $username:$username /home/$username
            fi

            # Create the full path for .ipython/profile_default/startup
            mkdir -p /home/$username/.ipython/profile_default/startup
            chown -R $username:$username /home/$username/.ipython

            # Now copy the cell hook
            cp /app/rapida_jupyter/az/cell_hook.py /home/$username/.ipython/profile_default/startup/cell_hook.py
            chown $username:$username /home/$username/.ipython/profile_default/startup/cell_hook.py

        else
            echo "Invalid user format: $user_info"
        fi
    done
fi


# Determine the port based on the PRODUCTION environment variable
if [ "$PRODUCTION" = "true" ]; then
    JUPYTER_PORT=80
else
    JUPYTER_PORT=8000
fi

# Start JupyterLab in the foreground (so the container keeps running)
pipenv run jupyterhub -f jupyterhub_config.py --port=$JUPYTER_PORT