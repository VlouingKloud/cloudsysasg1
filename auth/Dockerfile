FROM alpine

RUN apk update && apk add python3 && \
    apk add py3-pip && \
    pip3 install --upgrade pip && \
    pip3 install flask && \
    pip3 install bcrypt

WORKDIR /app

COPY . .

CMD ["python3", "main.py"]
