FROM python:3.12-slim-bookworm
WORKDIR /work
COPY requirements.txt /opt/font-build/requirements.txt
RUN pip install --no-cache-dir -r /opt/font-build/requirements.txt
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
COPY scripts /work/scripts
COPY sources /work/sources
COPY prompts /work/prompts
COPY README.md LICENSE Dockerfile compose.yaml requirements.txt .dockerignore .gitignore /work/
CMD ["sh", "scripts/build-docker.sh"]
