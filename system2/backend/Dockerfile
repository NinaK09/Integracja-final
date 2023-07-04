FROM tiangolo/uvicorn-gunicorn:python3.8

RUN mkdir -p /app

COPY requirements.txt /app

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . /app

CMD ["uvicorn", "backend-main:app", "--host", "0.0.0.0", "--port", "8080"]