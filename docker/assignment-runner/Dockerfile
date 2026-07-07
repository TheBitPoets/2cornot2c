FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libc6-dev python3 \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /usr/sbin/nologin runner

WORKDIR /workspace

USER runner

ENTRYPOINT ["python3", "/workspace/scripts/grade_activity.py"]
