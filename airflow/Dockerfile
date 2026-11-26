FROM node:22-bookworm-slim AS node
FROM apache/airflow:2.10.5-python3.12
USER root
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules/npm /usr/local/lib/node_modules/npm
RUN ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm && python -m venv /opt/research
COPY requirements.txt /tmp/lst-requirements.txt
RUN /opt/research/bin/pip install --no-cache-dir -r /tmp/lst-requirements.txt
USER airflow
