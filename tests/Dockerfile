FROM python:3.8

RUN mkdir /app/
WORKDIR /app/
COPY requirements.txt .
COPY test_data/ .

RUN pip install -r requirements.txt

COPY . .
ENTRYPOINT ["bash", "-c", "pytest -vs"]
