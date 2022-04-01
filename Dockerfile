FROM python:3.9

#include files
ADD main.py .
ADD .env .
#install external dependancies



LABEL maintainer="baglett   <thebaglett@gmail.com>"

CMD [ "python", "./main.py" ]