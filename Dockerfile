# Build felt/tippecanoe
# Dockerfile from https://github.com/felt/tippecanoe/blob/main/Dockerfile
FROM ubuntu:22.04 AS tippecanoe-builder

RUN apt-get update \
  && apt-get -y install build-essential libsqlite3-dev zlib1g-dev git

RUN git clone https://github.com/felt/tippecanoe
WORKDIR tippecanoe
RUN make


# Use the GDAL image as the base
FROM ghcr.io/osgeo/gdal:ubuntu-full-3.10.0

ARG GROUP_NAME="rapida"
ARG DATA_DIR='/data'
ARG PRODUCTION

ENV GROUP_NAME $GROUP_NAME
ENV DATA_DIR $DATA_DIR

# Install necessary tools and Python packages
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get update && \
    apt-get install -y python3-pip pipenv \
        gcc cmake libgeos-dev git vim sudo \
        ca-certificates curl gnupg nodejs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    npm install -g configurable-http-proxy

WORKDIR /app

# copy pyproject.toml to install dependencies
COPY pyproject.toml pyproject.toml
COPY README.md README.md

# install dev and jupyter dependencies
ENV PIPENV_VENV_IN_PROJECT=1
ENV PLAYWRIGHT_BROWSERS_PATH=0
RUN pipenv install --python 3 && \
    pipenv run pip install playwright && \
    pipenv run playwright install chromium --with-deps
ENV VIRTUAL_ENV=/app/.venv

# copy tippecanoe to production docker image
COPY --from=tippecanoe-builder /tippecanoe/tippecanoe* /usr/local/bin/
COPY --from=tippecanoe-builder /tippecanoe/tile-join /usr/local/bin/

# copy rapida_jupyter package and pyproject.toml to the image.
COPY rapida_jupyter /app/rapida_jupyter
COPY pyproject.toml /app/pyproject.toml
COPY README.md /app/README.md

# Conditional installation based on PRODUCTION variable
RUN if [ -z "$PRODUCTION" ]; then \
        pipenv run pip install -e . ; \
    else \
        pipenv run pip install . ; \
    fi
RUN pipenv --clear


# copy rest of files to the image.
COPY . .

RUN chmod +x /app/create_user.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]