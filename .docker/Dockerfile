ARG FRAPPE_PATH=https://github.com/frappe/frappe
ARG FRAPPE_BRANCH=version-15
ARG PYTHON_VERSION=3.11.6
ARG DEBIAN_BASE=bookworm
ARG NODE_VERSION=20.18.0

FROM ghcr.io/frappe/frappe_docker/build:v15

# Build args for app installation
ARG APPS_JSON_BASE64
ARG GITHUB_TOKEN

USER frappe
WORKDIR /home/frappe

# Decode apps.json from base64 build arg
RUN if [ -n "$APPS_JSON_BASE64" ]; then \
    echo "$APPS_JSON_BASE64" | base64 -d > /tmp/apps.json; \
  fi

# Initialize bench with frappe + clone all apps from apps.json
RUN bench init \
    --skip-redis-config-generation \
    --frappe-branch=${FRAPPE_BRANCH} \
    --frappe-path=${FRAPPE_PATH} \
    --apps_path=/tmp/apps.json \
    --no-procfile \
    frappe-bench

WORKDIR /home/frappe/frappe-bench

# Setup environment for apps
RUN echo "frappe" > sites/apps.txt && \
    ls apps | grep -v frappe >> sites/apps.txt || true

# Build assets for all apps (production-ready)
RUN bench setup requirements --node && \
    bench build --production && \
    bench setup requirements --python

# Final stage: lighter runtime image
FROM ghcr.io/frappe/frappe_docker/base:v15 AS runtime

USER frappe
WORKDIR /home/frappe

COPY --from=0 --chown=frappe:frappe /home/frappe/frappe-bench /home/frappe/frappe-bench

WORKDIR /home/frappe/frappe-bench

# Default command runs gunicorn for backend
CMD ["bench", "start"]
