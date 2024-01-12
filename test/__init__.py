# -*- coding: utf-8 -*-
# @Time    : 2023/12/15 上午1:27
# @Author  : sudoskys
# @File    : __init__.py.py

import asyncio

import requests
from requests import Response

openai_base_url = "http://127.0.0.1:10066/v1"


async def main() -> Response:
    tools = None
    tool_choice = None
    model = "gpt-3.5-turbo-0613"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + "test",
    }
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Who won the world series in 2020?"},
        {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
        {"role": "user", "content": "它在哪里举行的？"},
    ]
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
