from bs4 import BeautifulSoup
import configparser
from datetime import datetime
import os
import pathlib
import pymongo
import requests
import smtplib
import speedtest
import sys
import time
import tweepy


def get_mongo_conn(database: str, collection: str):
    client = pymongo.MongoClient()
    db = client[database]
    return db[collection]


def get_abs_path():
    return str(pathlib.Path(__file__).parent.absolute())


def append_to_file(filename: str, message: str):
    with open(filename, 'a+') as file:
        file.write(message)


def get_speed():
    st = speedtest.Speedtest()
    download = int(st.download()/1000/1000)
    upload = int(st.upload()/1000/1000)
    return download, upload


def get_system_path_slash():
    return '\\' if sys.platform == 'win32' else '/'


def convert_path_slashes(path=str):
    return path.replace('/', get_system_path_slash())


def send_tweet(body):
    config = get_config()
    consumer_key = config.get("TWITTER", "api_key")
    consumer_secret = config.get("TWITTER", "api_secret")
    access_token = config.get("TWITTER", "acess_token")
    access_token_secret = config.get("TWITTER", "access_secret")
    # authentication of consumer key and secret
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    # authentication of access token and secret
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    # update the status
    api.update_status(status=body)


def get_config():
    config = configparser.ConfigParser()
    config_path = '{abs}/{filepath}'.format(
        abs=get_abs_path(), filepath='config.ini')
    config.read(convert_path_slashes(config_path))
    return config


def get_page_content(URL):
    if URL is not None:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88Safari/537.36'}
        page = requests.get(URL, headers=headers)
        soup = BeautifulSoup(BeautifulSoup(
            page.content, 'html.parser').prettify(), 'html.parser')
        return soup


def find_wayfair_item_info(items):
    soup = get_page_content(items['url'])
    items['title'] = soup.findAll(
        "h1", {"class": "pl-Heading pl-Heading--pageTitle"})[0].get_text().strip()
    items['price'] = float(str(soup.findAll("div", {"class": "BasePriceBlock"})[
                           0].get_text().strip()).replace('$', ''))
    items['under_target'] = False
    return items


def send_email(item):
    config = get_config()
    server = smtplib.SMTP(config.get('GMAIL', 'host'),
                          int(config.get('GMAIL', 'port')))
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(user=config.get('GMAIL', 'email'),
                 password=config.get('GMAIL', 'password'))
    subject = '{title} - price fell! Now ${price}'.format(
        title=item['title'], price=item['price'])
    body = 'Check this link - {url} \n Price below target from ${target} to ${current_price}'.format(
        url=item['url'], target=item['target'], current_price=item['price'])
    msg = 'Subject: {subject}\n\n{body}'.format(subject=subject, body=body)
    server.sendmail(config.get('GMAIL', 'email'),
                    item['send_to'], msg)
    server.quit()


def products_to_price_check():
    data = []
    filepath = '{abs}/{filepath}'.format(abs=get_abs_path(),
                                         filepath='price_checker/products.txt')
    filepath = convert_path_slashes(filepath)
    with open(filepath, 'r') as file:
        for line in file:
            dictionary = {}
            currentline = line.split(',')
            dictionary['url'] = currentline[0]
            dictionary['target'] = float(currentline[1])
            dictionary['send_to'] = currentline[2].strip()
            dictionary['seller'] = currentline[3].strip()
            data.append(dictionary)
    return data


def get_info_for_items():
    items = products_to_price_check()
    for item in items:
        if item['seller'] == 'wayfair':
            item = find_wayfair_item_info(item)
    return items


def test_speed():
    variables = {'min_down': 50,
                 'pay_down': 1000,
                 'pay_up': 40,
                 'min_acceptable_down': 50,
                 'internet_prov': 'Comcast',
                 'loc': 'Burlington, MA'}

    download, upload = get_speed()
    variables['down'], variables['up'] = get_speed()
    collection = get_mongo_conn('mydbs', 'speed')
    
    insert = {"date": datetime.utcnow(),
              "download": download,
              "upload": upload}

    collection.insert_one(insert).inserted_id

    body = r"""Hey @{internet_prov} why is my internet speed {down} Mbps DOWN / {up} Mbps UP when I pay for {pay_down} Mbps down / {pay_up} Mbps up in {loc}? @ComcastCares @xfinity #comcast #speedtest""".format(
        **variables)

    if variables['down'] <= variables['min_acceptable_down']:
        send_tweet(body=body)


def price_checker():
    items = get_info_for_items()
    for item in items:
        print(item)
        if item['price'] <= item['target']:
            send_email(item)
