# -*- coding: utf-8 -*-
# @Time    : 2024/1/11 下午10:17
# @Author  : sudoskys
# @File    : search_exp.py
# @Software: PyCharm
import os
from pprint import pprint

from googleapiclient.discovery import build
from dotenv import load_dotenv
load_dotenv()
my_api_key = os.getenv("GOOGLE_API_KEY")  # Your API key
my_cse_id = os.getenv("GOOGLE_CSE_ID")  # Your search engine ID


def google_search(search_term, api_key, cse_id, **kwargs):
    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(q=search_term, cx=cse_id, **kwargs).execute()
    if 'items' not in res:
        pprint(res)
        print("No items in res")
        return []
    return res['items']


os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7897'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7897'
results = google_search('MYGO 是什么动漫？', my_api_key, my_cse_id, num=10)
for result in results:
    pprint(result)
