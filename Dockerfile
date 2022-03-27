FROM python:3.9

#include files
ADD main.py .

#install external dependancies
RUN pip install discord.py webhooks 

LABEL maintainer="baglett   <thebaglett@gmail.com>"

CMD [ "python", "./main.py" ]