FROM python:3.12
ENV PYTHONUNBUFFERED 1

RUN mkdir /app
WORKDIR /app
COPY req.txt /app/
RUN pip install --upgrade pip && pip install -r req.txt
ADD . /app/
WORKDIR /app/exceltopostgresql/
RUN chmod +x run.sh

ENTRYPOINT ["/app/exceltopostgresql/run.sh"]