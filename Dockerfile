FROM python:3.12-slim

WORKDIR /repo

COPY app/requirements.txt app/requirements.txt
RUN pip install --no-cache-dir -r app/requirements.txt

COPY app/ app/
COPY global/ global/
COPY casas/ casas/

CMD sh -c "cd /repo/app && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"
