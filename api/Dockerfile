FROM python:3.9
WORKDIR /app
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt && rm /code/requirements.txt
COPY ./immulogger /app/api
EXPOSE 80
ENV IMMUDB_HOST=immudb
ENV IMMUDB_PORT=3322
ENV IMMUDB_LOGIN=immudb
ENV IMMUDB_PASSWORD=immudb
ENV SECRET_KEY=09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "80"]