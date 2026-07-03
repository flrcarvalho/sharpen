FROM python:3.12-slim

WORKDIR /repo

COPY app/requirements.txt app/requirements.txt
RUN pip install --no-cache-dir -r app/requirements.txt

COPY app/ app/
COPY global/ global/
COPY casas/ casas/

# Usuário não-root: reduz o impacto de uma eventual execução de código no container.
RUN useradd --create-home --uid 10001 appuser
USER appuser

# Liveness: bate no /healthz (sem auth, não toca o banco). Usa a PORT do ambiente.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('PORT','8000')+'/healthz').read()" || exit 1

CMD sh -c "cd /repo/app && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"
