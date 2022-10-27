FROM python:3.8.10
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
COPY . /code/
ADD  https://link.storjshare.io/s/jvlzn7kdude3agzudlyhj6yb63sq/xeyem/data.zip?download=1 .
RUN ls
RUN unzip data.zip