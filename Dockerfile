FROM python:3.12

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONNUNBUFFERED=1

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "main.py" ]