FROM python

RUN pip install flask
RUN pip install pymongo

COPY  ./static /home/myapp/static/
COPY  ./templates /home/myapp/templates/
COPY  app.py /home/myapp/

EXPOSE 8080

CMD python /home/myapp/app.py