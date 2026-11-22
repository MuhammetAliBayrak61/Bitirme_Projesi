FROM apache/airflow:2.10.5-python3.12
USER root
RUN python -m venv /opt/research
COPY requirements.txt /tmp/lst-requirements.txt
RUN /opt/research/bin/pip install --no-cache-dir -r /tmp/lst-requirements.txt
USER airflow
