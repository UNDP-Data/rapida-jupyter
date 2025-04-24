# rapida-jupyter
Jupyter Hub for RAPIDA tool

## Development

This repository uses Docker to launch Jupyter Hub locally. Makefile provides you necessary commands to setup Jupyter Hub.

- Build Docker image

```shell
make build
```

If you would like to build image for production, execute the below command

```shell
PRODUCTION=true make build
```

- Launch Jupyter Hub

```shell
make up
```

You can access to JupyterHub through `http:localhost:8100` in your browser. 

- set users

Authenticate users can be set through `JUPYTER_USERS` variable at `.env` file.

```
cp .env.example .env
vi .env
```

JUPYTER_USERS can have multiple users (username:password) for authentication

```shell
JUPYTER_USERS=docker:docker user:user
```

folder structure in the container will be as follows:

- /data - it will be mounted to fileshare in Azure. All files under this folder will be kept
  - /data/{username} - users can explore all users file, a user has no permission to edit other users' folder.
- /home/{username} - user home folder. This data will be lost when the server is restarted.

### destroy docker container

```shell
make down
```

### enter to Docker container

```shell
make shell
```

Note. if you use `make shell`, entrypoint.sh is not executed. That means you have to install RAPIDA tool manually like below.

```shell
pipenv run pip install git+https://github.com/UNDP-Data/rapida
```