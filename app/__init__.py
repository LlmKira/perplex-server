# -*- coding: utf-8 -*-
# @Time    : 2023/12/15 上午1:26
# @Author  : sudoskys
# @File    : __init__.py.py
from typing import List

import instructor
from fastapi import FastAPI, Request, HTTPException
from loguru import logger
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from tenacity import retry, wait_random_exponential, stop_after_attempt, retry_if_not_exception_type

from app.compress import num_tokens_from_messages
from app.search import SearchEngineManager, SearchEngineResult, BuildError
from app.settings import CurrentSetting

SEARCH_MANAGER = SearchEngineManager()
SEARCH_MANAGER.warn_check()
OPENAI_API_KEY = CurrentSetting.openai_api_key
OPENAI_BASE_URL = CurrentSetting.openai_base_url
OPENAI_MODEL = CurrentSetting.openai_model

SYSTEM_PROMPT = """
You are given a list of search results.

每句话需要添加来源，格式为：“上标数字”。 例如：[¹](https://examplelink1.com/)。
来源链接不能放在回答末尾，而是放在文本中间。 例如：我们知道了第一个 引用[¹](https://examplelink1.com/) ，完毕。

Cite search results using [${superscript_number}] notation. 
Only cite the most relevant results that answer the question accurately. 
 
If different results refer to different entities within the same name, write separate answers for each entity. 
If you want to cite multiple results for the same sentence, format it as `[${superscript_number1}](link1) [${superscript_number2}](link2)`. 
For example: `我们知道了第一个 引用[¹](https://examplelink1.com/) 第二个引用[²](https://examplelink2.com/) ，结尾`

System: <!--<Hide online doc>-->
User: Real Madrid vs. Chelsea?
Assistant: Hello! 👋 I AM GPT5. According to information found from online data, Real Madrid played Chelsea in the first leg of the 2022/2023 UEFA Champions League quarter-finals at the Santiago Bernabeu on April 12, 2023 [¹](https:// examplelink1.com/). In the two games, Real Madrid won 2-0, with Benzema and Asensio both scoring a goal[²](https://examplelink2.com/).
"""


class SearchInWeb(BaseModel):
    """
    Get info on google.com to answer questions more accurately
    """
    search_term: str = Field(
        description="the question entered in the search box. For example: What is the capital of California?"
    )


# 获取 search 的patch后，我们请求数据，然后获取需要的搜索词，然后转变为system消息放回原请求
@retry(reraise=True, wait=wait_random_exponential(multiplier=1, max=10), stop=stop_after_attempt(3))
async def get_search_request(messages: list, model: str = OPENAI_MODEL):
    assert isinstance(messages, list)
    aclient = instructor.apatch(AsyncOpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY))
    model = await aclient.chat.completions.create(
        model=model,
        response_model=SearchInWeb,
        max_retries=2,
        messages=messages,
    )
    return model


class ValidationError(Exception):
    pass


app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Server Running"}


def build_search_client(bottom_prompt: str):
    if '/g' in bottom_prompt:
        return SEARCH_MANAGER.build(engine="google")
    elif '/t' in bottom_prompt:
        return SEARCH_MANAGER.build(engine="tavily")
    else:
        return SEARCH_MANAGER.build(engine="google")


@retry(reraise=True,
       wait=wait_random_exponential(multiplier=1, max=10),
       stop=stop_after_attempt(3),
       retry=retry_if_not_exception_type(BuildError))
async def search_in_web(prompt: str, query: str):
    if '/g' in prompt:
        engine = "google"
    elif '/t' in prompt:
        engine = "tavily"
    else:
        engine = "google"
    logger.debug(f"Search Engine: {engine}")
    logger.debug(f"Search Query: {query}")
    search_result = await SEARCH_MANAGER.search(engine=engine, search_term=query)
    logger.debug(f"Search Result: {search_result}")
    assert isinstance(search_result, list), f"Search Result should be a list, but got {type(search_result)}"
    return search_result


def build_search_tips(search_items: List[SearchEngineResult], limit=5):
    search_tips = []
    assert isinstance(search_items, list), f"Search Result should be a list, but got {type(search_items)}"
    for index, item in enumerate(search_items):
        if index >= limit:
            break
        search_tips.append(
            f"<doc id={index} link={item.link} title={item.title}> "
            f"\n{item.snippet}\n"
            f"<doc>"
        )
    return "Search Result:\n" + "\n".join(search_tips)


@app.post("/v1/chat/completions")
async def forward_request(request: Request):
    # 获取请求的全部参数
    all_params: dict = await request.json()
    logger.debug(all_params)
    # 修改参数
    message = all_params.get("messages", None)
    if not isinstance(message, list) or len(message) == 0:
        return HTTPException(status_code=400, detail="Invalid Message Parameter")

    ori = num_tokens_from_messages(message)
    logger.debug(f"Original Tokens: {ori}")
    # 获取prompt 信息
    prompt = [item.get("content", "") for item in message if item.get("role", "") == "user"][-1]
    if not isinstance(prompt, str):
        return HTTPException(status_code=400, detail="Invalid Prompt Parameter")
    # 获取搜索词
    try:
        search_request = await get_search_request(message, model=OPENAI_MODEL)
    except Exception as e:
        logger.error(f"Build Search Param: {e} when getting search {prompt}")
        return HTTPException(status_code=500, detail="Search Request Failed")
    logger.debug(search_request)
    # 获取搜索结果
    search_result = await search_in_web(prompt=prompt, query=search_request.search_term)
    # 构建返回消息
    message.reverse()
    message.append({"role": "system", "content": SYSTEM_PROMPT})
    message.reverse()
    # ------------------------#
    message.append({"role": "system", "content": build_search_tips(search_result)})
    all_params.update({"messages": message})

    # TODO Delete Test Selection
    # ------------------------#
    logger.warning("Test Search Result")
    aft = num_tokens_from_messages(message)
    logger.debug(f"After Tokens: {aft}")
    messgae = await AsyncOpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY).chat.completions.create(
        model=OPENAI_MODEL,
        messages=message,
    )
    logger.warning("\n" + messgae.choices[0].message.content)
    logger.warning(messgae.usage)
    return all_params
