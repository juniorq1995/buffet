FROM python:3
ADD main.py /
#RUN pip install argparse simplejson datetime
CMD [ "python", "./main.py" ]