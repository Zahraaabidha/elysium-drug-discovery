# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# system deps (if RDKit or other heavy libs are needed you may need a different base)
RUN apt-get update && apt-get install -y build-essential git curl && rm -rf /var/lib/apt/lists/*

# copy requirements first to leverage layer caching
COPY backend/requirements.txt ./requirements.txt

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# copy app code
COPY backend/ ./

# runtime env
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# expose
EXPOSE 8000

# run uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--reload"]
