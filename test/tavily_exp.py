# -*- coding: utf-8 -*-
# @Time    : 2024/1/12 下午12:01
# @Author  : sudoskys
# @File    : tavily.py
# @Software: PyCharm
import os
from pprint import pprint

from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
# For basic search:
response = tavily.search(query="孤独摇滚是什么动漫？", search_depth="basic")
pprint(response)
# Get the search results as context to pass an LLM:
context = [{"url": obj["url"], "content": obj["content"]} for obj in response.get("results")]
pprint(context)
