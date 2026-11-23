FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Run as a non-root user (required by many K8s security policies)
RUN useradd --create-home --uid 10001 chat
WORKDIR /app
COPY chatterbox/ ./chatterbox/
USER 10001

EXPOSE 5000
# Exec form so SIGTERM from Kubernetes reaches Python directly
CMD ["python", "-m", "chatterbox.server"]
