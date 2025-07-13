FROM python:3.12
ENV PYTHONUNBUFFERED 1

RUN mkdir /app
WORKDIR /app
COPY req.txt /app/
RUN pip install --upgrade pip && pip install -r req.txt
ADD . /app/
WORKDIR /app/table_service/

ENTRYPOINT ["python manage.py runserver 0.0.0.0:8000"]