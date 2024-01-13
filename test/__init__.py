# -*- coding: utf-8 -*-
# @Time    : 2023/12/15 上午1:27
# @Author  : sudoskys
# @File    : __init__.py.py

import asyncio

import requests
from requests import Response

openai_base_url = "http://127.0.0.1:10066/v1"
exp1 = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Who won the world series in 2020?"},
    {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
    {"role": "user", "content": "它在哪里举行的？"},
]

exp2 = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "/g 介绍一下孤独摇滚动漫？"},
]

exp3 = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "/g 孤独摇滚的主要剧情是什么？"},
]

exp4 = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "/t 扳机社都有哪些作品"},
]

exp5 = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "/g 芝士雪豹是什么？"},
]


async def main() -> Response:
    tools = None
    tool_choice = None
    model = "gpt-3.5-turbo-0613"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + "test",
    }
    messages = exp3
    json_data = {"model": model, "messages": messages}
    if tools is not None:
        json_data.update({"tools": tools})
    if tool_choice is not None:
        json_data.update({"tool_choice": tool_choice})
    print(json_data)
    response = requests.post(
        f"{openai_base_url}/chat/completions",
        headers=headers,
        json=json_data,
    )
    print(response.json())
    return response


asyncio.run(main())
