FROM python:3
ADD main.py /
RUN pip install psycopg2 requests numpy pandas datetime
CMD [ "python", "./main.py" ]