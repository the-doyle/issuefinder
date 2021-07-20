FROM python:3.7-slim-buster

WORKDIR /IssueFinder

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY . /IssueFinder/

CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]

# # setup environment variable  
# ENV DockerHOME=/app

# # set working directory  
# RUN mkdir -p $DockerHOME  
# ENV PYTHONDONTWRITEBYTECODE 1
# ENV PYTHONUNBUFFERED 1  

# # where your code lives  
# WORKDIR $DockerHOME  

# ADD . ${DockerHOME}

# COPY ./requirements.txt /app/requirements.txt

# RUN pip install -r requirements.txt

# COPY . /app