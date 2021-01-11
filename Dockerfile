FROM python:3.9-slim

COPY *.py /root
RUN pip install beautifulsoup4 dateparser lxml rfeed urllib3