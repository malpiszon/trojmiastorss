FROM python:3.9-slim

COPY *.py /root
COPY web /root/web
RUN pip install beautifulsoup4 dateparser lxml rfeed urllib3
