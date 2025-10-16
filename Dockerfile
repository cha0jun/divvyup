FROM python:3.12-slim

WORKDIR /app

COPY /app /app

RUN pip install "fastapi[standard]"==0.117.1

ENV PORT=8000
ENV ENVIRONMENT=production

EXPOSE $PORT

CMD ["fastapi", "run", "/app/main.py"]