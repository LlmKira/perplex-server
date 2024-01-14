# -*- coding: utf-8 -*-
# @Time    : 2023/12/15 上午1:27
# @Author  : sudoskys
# @File    : __init__.py.py

import asyncio
import time
from getpass import getpass

import requests
from loguru import logger
from openai import AsyncOpenAI
from requests import Response
from rich.console import Console

from app import CurrentSetting
from app.compress import num_tokens_from_messages

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
    {"role": "user", "content": "/s 孤独摇滚的主要剧情是什么？"},
]

exp4 = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "/s Bang Dream ItsMyGo的主要剧情是什么？"},
]

exp5 = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "/g 芝士雪豹是什么？"},
]
OPENAI_API_KEY = CurrentSetting.openai_api_key
OPENAI_BASE_URL = CurrentSetting.openai_base_url
OPENAI_MODEL = CurrentSetting.openai_model


async def main(prompt) -> Response:
    time1 = int(time.time() * 1000)
    tools = None
    tool_choice = None
    model = "gpt-3.5-turbo-0613"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + "test",
    }
    message = [
        {"role": "user", "content": prompt},
    ]
    messages = message
    json_data = {"model": model, "messages": messages}
    if tools is not None:
        json_data.update({"tools": tools})
    if tool_choice is not None:
        json_data.update({"tool_choice": tool_choice})
    print(json_data)
    ori = num_tokens_from_messages(messages)
    logger.debug(f"Original Tokens: {ori}")
    response = requests.post(
        f"{openai_base_url}/chat/completions",
        headers=headers,
        json=json_data,
    )
    print(response.json())
    time2 = int(time.time() * 1000)
    cost_time = int((time2 - time1) / 1000)
    logger.info(f"Perplex Server Cost Time: {time2 - time1} ms as {cost_time} s")
    # TODO Delete Test Selection
    # ------------------------#
    message = response.json()["messages"]
    logger.warning("Test Search Result")
    aft = num_tokens_from_messages(message)
    logger.debug(f"After Tokens: {aft}")
    messgae = await AsyncOpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY).chat.completions.create(
        model=OPENAI_MODEL,
        messages=message,
    )
    result_message = messgae.choices[0].message.content
    logger.warning("\n" + result_message)
    logger.warning(messgae.usage)
    # ------------------------#
    from rich.table import Table
    table = Table()
    table.add_column('[pink]Prompt')
    table.add_column('[pink]Result')
    table.add_row(f'[pink]{prompt}', f'[yellow]{ori}token origin')
    table.add_row(f'[green] Search Cost {cost_time}s ', f'[yellow]{aft}token after')
    table.add_row(f'[bold]Total Tokens {messgae.usage.total_tokens} [/bold]', f"Model {OPENAI_MODEL}")
    table.add_row('[bold magenta] Tips: /t-tavily /g-google /s-serper [/bold magenta]')
    console = Console(color_system='256', style=None)
    console.print(table)
    console.print(result_message)
    await asyncio.sleep(3)
    return response


while True:
    asyncio.run(main(getpass()))
