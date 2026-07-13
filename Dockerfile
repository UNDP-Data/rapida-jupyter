# ==========================================
# STAGE 1: Node Proxy Builder
# ==========================================
# Use the official Node image to guarantee version and integrity
FROM node:22-slim AS node-builder
RUN npm install -g configurable-http-proxy

# ==========================================
# STAGE 2: Final Jupyter Runtime
# ==========================================
# Inherit directly from your new CI-built base
FROM ghcr.io/undp-data/rapida:latest

# Switch to root to install system-level proxy dependencies
USER root

ARG APP_DIR="/app"
ARG GROUP_NAME="rapida"
ARG DATA_DIR="/data"
ARG PRODUCTION

ENV APP_DIR=$APP_DIR
ENV GROUP_NAME=$GROUP_NAME
ENV DATA_DIR=$DATA_DIR

# 1. Inject the pure Node executable
COPY --from=node-builder /usr/local/bin/node /usr/local/bin/

# 2. Inject the fully compiled proxy package (leaving npm and cache behind!)
COPY --from=node-builder /usr/local/lib/node_modules/configurable-http-proxy /usr/local/lib/node_modules/configurable-http-proxy

# 3. Create the symlink so JupyterHub can find the proxy command
RUN ln -s /usr/local/lib/node_modules/configurable-http-proxy/bin/configurable-http-proxy /usr/local/bin/configurable-http-proxy

# Install ONLY the necessary system tools (sudo). No more curl or nodesource!
RUN grep -lr 'apache.jfrog.io' /etc/apt/sources.list.d/ | xargs -r rm -f && \
    apt-get update && \
    apt-get install -y --no-install-recommends sudo && \
    apt-get autoremove -y && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR $APP_DIR

# ==========================================
# DEPENDENCY LAYER CACHING
# ==========================================
COPY  pyproject.toml README.md ./

# Use uv to install external dependencies lightning fast
RUN uv pip install --compile .

# ==========================================
# APPLICATION CODE & LOCAL INSTALL
# ==========================================
COPY . .

RUN if [ -z "$PRODUCTION" ]; then \
        uv pip install --compile -e . ; \
    else \
        uv pip install --compile . ; \
    fi

# ==========================================
# PERMISSIONS & ENTRYPOINT
# ==========================================
RUN groupadd -f ${GROUP_NAME} && \
    usermod -aG ${GROUP_NAME} root && \
    chown -R :${GROUP_NAME} $APP_DIR && \
    chmod -R g+rwx $APP_DIR && \
    mkdir -p $DATA_DIR && \
    chown -R :${GROUP_NAME} $DATA_DIR && \
    chmod +x $APP_DIR/create_user.sh && \
    chmod +x $APP_DIR/entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
