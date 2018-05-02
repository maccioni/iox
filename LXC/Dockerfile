FROM alpine:3.5

RUN apk add --update \
    python3

RUN pip3 install bottle

EXPOSE 8000

COPY main.py /main.py
