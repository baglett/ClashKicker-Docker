FROM python:3.9

#include files
ADD main.py .
# ADD .env .
#install external dependancies
RUN pip install pymysql
RUN pip install python-dotenv
RUN pip install schedule



LABEL maintainer="baglett   <thebaglett@gmail.com>"

CMD [ "python", "./main.py" ]