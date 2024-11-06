FROM python:3.9

WORKDIR /app

COPY requirements.txt .

RUN apt-get update && apt-get install -y libsentencepiece-dev

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]