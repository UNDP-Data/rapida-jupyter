#!/bin/bash

# ==========================================================
# DEPENDENCIES ARE NOW HANDLED IN DOCKERFILE
# GDAL and rapida are pre-compiled in the rapida:latest base
# ==========================================================

# Create multiple users from environment variable JUPYTER_USERS
# Format: JUPYTER_USERS="user1:password1 user2:password2 user3:password3"

if [ ! -z "$JUPYTER_USERS" ]; then

    # Ensure runtime permissions on the data directory (in case of volume mounts)
    mkdir -p $DATA_DIR
    #chown -R :${GROUP_NAME} $DATA_DIR

    NOTEBOOKS_DIR=${DATA_DIR}/notebooks_templates

    if [ ! -d "${NOTEBOOKS_DIR}" ]; then
        mkdir -p ${NOTEBOOKS_DIR}
    fi

    # CORRECTED: Pointing to /app
    cp -r /app/notebooks/. ${NOTEBOOKS_DIR}/.

    # Set permissions so that users in GROUP_NAME can write to /data/notebooks
    chown -R :${GROUP_NAME} ${NOTEBOOKS_DIR}
    chmod -R g+rwX ${NOTEBOOKS_DIR}

    for user_info in $JUPYTER_USERS; do
        IFS=':' read -r username password <<< "$user_info"
        if [ ! -z "$username" ] && [ ! -z "$password" ]; then

            # CORRECTED: Pointing to /app
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

            home_dir=$(eval echo "~$username")

            # Source the venv from the base image (/rapida/.venv)
            sudo -u "$username" bash -c "source /rapida/.venv/bin/activate && cd \"$home_dir\" && rapida init --no-input" 2>&1 | tee "/var/log/rapida_init_$username.log"

            # CORRECTED: Pointing to /app
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

# Start JupyterHub directly
jupyterhub -f jupyterhub_config.py --port=$JUPYTER_PORT