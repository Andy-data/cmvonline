# To enable ssh & remote debugging on app service change the base image to the one below
# FROM mcr.microsoft.com/azure-functions/python:3.0-python3.7-appservice
FROM mcr.microsoft.com/azure-functions/python:3.0-python3.7
 

ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true

COPY requirements.txt /
RUN apt-get install -y g++
RUN hash -r
RUN set
RUN pip install -r /requirements.txt

WORKDIR /home/site/wwwroot

COPY . .
EXPOSE 8050:80

ENTRYPOINT [ "flask", "run" ]
# RUN python /home/site/wwwroot/CMV_online.py
