FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN nvidia-smi

CMD ["python", "app.py"]
