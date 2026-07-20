FROM debian:bookworm-slim

# Immagine minimale per i runner C, Python, Node.js e SQLite.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libc6-dev python3 nodejs sqlite3 \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /usr/sbin/nologin runner

WORKDIR /workspace

USER runner

ENTRYPOINT ["python3", "/workspace/scripts/grade_activity.py"]
