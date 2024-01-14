# -*- coding: utf-8 -*-
# @Time    : 2024/1/14 下午4:11
# @Author  : sudoskys
# @File    : serper.py
# @Software: PyCharm
import json
import os

import requests
from dotenv import load_dotenv
from rich.pretty import pprint

url = "https://google.serper.dev/search"

payload = json.dumps({
    "q": "孤独摇滚"
})
load_dotenv()
headers = {
    'X-API-KEY': os.getenv("SERPER_API_KEY"),
    'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload)

pprint(response.text)

pprint(response.json())
