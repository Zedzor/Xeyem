# Xeyem

This is a web application for criptocurrency forensics investigations. Supported tokens: **Bitcoin (BTC)** and **Ethereum (ETH)**

## Deployment
There are 2 ways of deploying this app: Docker and manually

### Docker
Execute `docker-compose up` while being on the same directory as the **docker-compose.yml** file.

**Note**: It may take a while since it downloads the database with the loaded datasets and the dataset files.

The app will be running on **http://localhost:8888**

### Manually
+ Python version used `3.8.10`

+ Upgrade pip `pip install --upgrade pip`

+ Install required python packages `pip install -r requirements.txt`

+ Download the dataset files on **https://link.storjshare.io/s/jvlzn7kdude3agzudlyhj6yb63sq/xeyem/data.zip?download=1**

+ Unzip them on the same directory as manage.py

+ Run the app `python manage.py runserver`


## Loading datasets manually

For loading datasets manually execute the following commands.

```sh
rm db.sqlite3

wget https://link.storjshare.io/s/jvlzn7kdude3agzudlyhj6yb63sq/xeyem/data.zip?download=1 -O data.zip

unzip data.zip

python manage.py makemigrations

python manage.py migrate

python manage.py runscript load_data

python manage.py runserver
```
