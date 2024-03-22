FROM python:3.12

# Install deps
COPY ./requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

WORKDIR /usr/src/app/
COPY ./src ./src
COPY ./migrations ./migrations
COPY ./briv.json ./briv.json

# Run app
EXPOSE 3000
CMD ["uvicorn", "--host", "0.0.0.0", "--port", "3000", "src.main:app"]