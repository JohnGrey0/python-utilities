import glob
import pathlib
import os
import random
import re
import requests
import shutil
import sys
import time
import wget
import zipfile
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options as COptions
from selenium.webdriver.firefox.options import Options as FOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from sys import platform


class web:
    def __init__(self):
        self.user_agent = UserAgent()
        self.headers = {
            'User-Agent': self.user_agent.random
        }
        self.os_slash = '\\' if sys.platform == 'win32' else '/'
        self.webdriver_executable_path = ''

    def req_response(self, url: str):
        if self.validate_url(unvalidated_url=url):
            response = requests.get(url=url, headers=self.headers)
            return response

    def bs4_content(self, page_source):
        page = page_source
        soup = BeautifulSoup(BeautifulSoup(
            page.content, 'html.parser').prettify(), 'html.parser')
        return soup

    def send_request(self, url: str, payload: dict, type: str):
        if type is not None and self.validate_url(unvalidated_url=url):
            if str.lower(type) == 'post':
                response = requests.post(url=url, data=payload, verify=False)
                return response.text
            elif str.lower(type) == 'get':
                response = requests.get(url=url, params=payload, verify=False)
                return response.json()

    def get_dynamic_content(self, url: str,  chrome=False, firefox=False, headless=False):
        if self.validate_url(unvalidated_url=url):
            driver = self.get_webdriver(
                chrome=chrome, firefox=firefox, headless=headless)
            driver.get(url)
            time.sleep(3)
            html = driver.page_source
            driver.quit()
            return html

    def login_site(self, **kwargs):
        url = kwargs.pop('url', None)
        keys = kwargs.pop('keys', None)
        chrome = kwargs.pop('chrome', False)
        firefox = kwargs.pop('firefox', False)
        headless = kwargs.pop('headless', False)

    def set_webdriver_version(self, browser: str):
        if browser == 'chrome':
            self.webdriver_executable_path = '{cwd}{slash}webdrivers{slash}chromedriver.exe'.format(cwd=os.getcwd(), slash=self.os_slash) if sys.platform == 'win32'  else '{cwd}{slash}webdrivers{slash}chromedriver'.format(cwd=os.getcwd(), slash=self.os_slash)
        elif browser == 'firefox':
            self.webdriver_executable_path = '{cwd}{slash}webdrivers{slash}geckodriver.exe'.format(cwd=os.getcwd(), slash=self.os_slash) if sys.platform == 'win32'  else '{cwd}{slash}webdrivers{slash}geckodriver'.format(cwd=os.getcwd(), slash=self.os_slash)

    def get_webdriver(self, chrome=False, firefox=False, headless=False):
        if self.check_if_webdriver_exists(chrome=chrome):
            chrome_options = COptions()
            if headless:
                chrome_options.add_argument("--headless")
            driver = webdriver.Chrome(
                executable_path=self.webdriver_executable_path, chrome_options=chrome_options)
            return driver
        elif self.check_if_webdriver_exists(firefox=firefox):
            driver = webdriver.Chrome(
                executable_path=self.webdriver_executable_path)
            return driver

    def check_if_webdriver_exists(self, chrome=False, firefox=False):
        driver = 'chrome' if chrome else 'firefox' if firefox else None
        if driver is not None:
            self.set_webdriver_version(browser=driver)
            drivers = {
                'chrome': self.webdriver_executable_path,
                'firefox': self.webdriver_executable_path 
            }
            driver_location = drivers[driver]
            if os.path.isfile(driver_location):
                return True
            else:
                return self.download_webdriver(driver=driver)
        return False

    def validate_url(self, unvalidated_url: str):
        if unvalidated_url is not None:
            regex = re.compile(
                r'^(?:http|ftp)s?://'  # http:// or https://
                # domain...
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
                r'localhost|'  # localhost...
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
                r'(?::\d+)?'  # optional port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            return (re.match(regex, unvalidated_url) is not None)

    def download_file(self, url: str, filename='default.file'):
        if self.validate_url(unvalidated_url=url):
            download_dir = '{cwd}{slash}downloads{slash}'.format(
                cwd=os.getcwd(), slash=self.os_slash)
            if os.path.isdir(download_dir):
                self.remove_folder_contents(folder=download_dir)
            else:
                os.mkdir(download_dir)
            file_name = '{cwd}{slash}downloads{slash}{filename}'.format(
                cwd=os.getcwd(), slash=self.os_slash, filename=filename)
            wget.download(url, file_name)
            return file_name

    def unzip_download(self, old_loc: str, new_loc: str):
        with zipfile.ZipFile(old_loc, 'r') as zip_ref:
            zip_ref.extractall(new_loc)

    def remove_folder_contents(self, folder: str):
        file_wildcard = '{dir}{slash}*'.format(dir=folder, slash=self.os_slash)
        files = glob.glob(file_wildcard)
        for file in files:
            os.remove(file)

    def find_all_links(self, url: str, str_to_match: str):
        links = []
        match = "^{match}".format(match=str_to_match)
        if self.validate_url(unvalidated_url=url):
            soup = self.bs4_content(self.req_response(url=url))
            for link in soup.findAll('a', attrs={'href': re.compile(match)}):
                links.append(link.get('href'))
            return links

    def download_webdriver(self, driver: str):
        driver_links = {
            'chrome': {
                'win32': 'https://chromedriver.storage.googleapis.com/79.0.3945.36/chromedriver_win32.zip',
                'linux2': 'https://chromedriver.storage.googleapis.com/79.0.3945.36/chromedriver_linux64.zip',
                'darwin': 'https://chromedriver.storage.googleapis.com/79.0.3945.36/chromedriver_mac64.zip'
            },
            'firefox': {
                'win32': 'https://github.com/mozilla/geckodriver/releases/download/v0.26.0/geckodriver-v0.26.0-win64.zip',
                'linux2': 'https://github.com/mozilla/geckodriver/releases/download/v0.26.0/geckodriver-v0.26.0-linux64.tar.gz',
                'darwin': 'https://github.com/mozilla/geckodriver/releases/download/v0.26.0/geckodriver-v0.26.0-macos.tar.gz'
            },
        }
        filename = 'chromedriver' if driver == 'chrome' else 'geckodriver' if driver == 'firefox' else None
        zip_file = self.download_file(url=driver_links[driver][sys.platform], filename='{name}'.format(
            slash=self.os_slash, name=filename))
        # print(os.pathsep + os.pathsep.join(['{cwd}{slash}webdrivers{slash}'.format(cwd=os.getcwd(), slash=self.os_slash)]))
        loc = '{cwd}{slash}webdrivers{slash}'.format(
            cwd=os.getcwd(), slash=self.os_slash, filename=filename)
        self.unzip_download(old_loc=zip_file, new_loc=loc)
        if sys.platform == 'win32':
            pass
        else:
            os.chmod(self.webdriver_executable_path, mode=0o755)
        return True
