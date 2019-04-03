FROM python:3.7

MAINTAINER Will Pearson "will@mcneel.com"

WORKDIR /app

COPY ./requirements.txt .

RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["flask", "run", "-h", "0.0.0.0"]