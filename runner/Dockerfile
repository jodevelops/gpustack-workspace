FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    MPLCONFIGDIR=/tmp/matplotlib

COPY requirements.txt /opt/workroom/requirements.txt
RUN python -m pip install --no-cache-dir -r /opt/workroom/requirements.txt \
    && python -m pip check

WORKDIR /output
USER 65534:65534
CMD ["python", "/task.py"]
