# -*- coding: utf-8 -*-
# @Time    : 2023/12/15 上午1:26
# @Author  : sudoskys
# @File    : __init__.py.py
import time
from typing import List

import instructor
from fastapi import FastAPI, Request, HTTPException
from loguru import logger
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from tenacity import retry, wait_random_exponential, stop_after_attempt, retry_if_not_exception_type

from app.search import SearchEngineManager, SearchEngineResult, BuildError
from app.settings import CurrentSetting

SEARCH_MANAGER = SearchEngineManager()
SEARCH_MANAGER.warn_check()
OPENAI_API_KEY = CurrentSetting.openai_api_key
OPENAI_BASE_URL = CurrentSetting.openai_base_url
OPENAI_MODEL = CurrentSetting.openai_model

SENSOR_PROMPT = """Tips:
"""

SYSTEM_PROMPT = """
You are given a list of knowledge points, **answer users in creatively and in detail.**

[Obey Following Rule]
- EVERY SENTENCE NEED A SOURCE, IN THE FORMAT OF "[INDEX:SUPERSCRIPT FORMAT](SOURCE LINK)". FOR EXAMPLE: [¹](HTTPS://EXAMPLELINK1.COM/).
- MARKERS MUST BE WITH LINKS OF ONLINE DATA.
- RECOMMENDED PRIORITIZE USE OF ONLINE DATA.
- YOUR ANSWERS SHOULD AVOID PROVIDING OUTDATED, NON-EXISTENT, OR FALSE INFORMATION, AS WELL AS INCORRECT FORMAT.
- ONLY CITE THE MOST RELEVANT RESULTS THAT ANSWER THE QUESTION ACCURATELY. 
- IF DIFFERENT RESULTS REFER TO DIFFERENT ENTITIES WITHIN THE SAME NAME, WRITE SEPARATE ANSWERS FOR EACH ENTITY. 
- IF YOU WANT TO CITE MULTIPLE RESULTS FOR THE SAME SENTENCE, FORMAT IT AS `[$SUPERSCRIPT NUMBER1](LINK1) [$SUPERSCRIPT NUMBER2](LINK2)`. 
- CITE SEARCH RESULTS USING [$SUPERSCRIPT NUMBER] NOTATION. 

[Answer Format:strict mode]
    Format:
       <!--body: 遵守引用格式[¹](https://examplelink1.com/) 按照标注WIKI标注[²](https://examplelink2.com/) --> 
       <!--refer: 参考部分 -->
    
    Example:
       这个问题[¹](https://examplelink1.com/) 的答案是[²](https://examplelink2.com/)。
       请参考： 
       [¹] [title1](https://examplelink1.com/) 
       [²] [title2](https://examplelink2.com/)
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
    now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    now_time_prompt = f"<CurrentTime={now_time}>"
    messages.append({"role": "system", "content": f"{SENSOR_PROMPT}{now_time_prompt}"})
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


def check_prompt(prompt: str):
    engine = None
    if prompt.strip().startswith("/g"):
        engine = "google"
    elif prompt.strip().startswith("/t"):
        engine = "tavily"
    elif prompt.strip().startswith("/s"):
        engine = "serper"
    if engine is None:
        raise ValidationError("Invalid Prompt Parameter")
    else:
        return engine


@retry(reraise=True,
       wait=wait_random_exponential(multiplier=1, max=10),
       stop=stop_after_attempt(3),
       retry=retry_if_not_exception_type(BuildError))
async def search_in_web(query: str, engine: str):
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
    return "Search Api:\n" + "\n".join(search_tips)


@app.post("/v1/chat/completions")
async def forward_request(request: Request):
    # 获取请求的全部参数
    all_params: dict = await request.json()
    logger.debug(all_params)
    # 修改参数
    message = all_params.get("messages", None)
    if not isinstance(message, list) or len(message) == 0:
        return HTTPException(status_code=403, detail="Invalid Message Parameter")
    # 获取prompt 信息
    prompt = [item.get("content", "") for item in message if item.get("role", "") == "user"][-1]
    if not isinstance(prompt, str):
        return HTTPException(status_code=403, detail="Invalid Prompt Parameter")
    # 获取搜索词
    try:
        engine = check_prompt(prompt)
    except ValidationError as e:
        logger.error(f"Check Prompt: {e} when getting prompt {prompt}")
        return HTTPException(status_code=401, detail="No Flag Found")
    try:
        search_request = await get_search_request(message, model=OPENAI_MODEL)
    except Exception as e:
        logger.error(f"Build Search Param: {e} when getting search {prompt}")
        return HTTPException(status_code=402, detail="Build search_term Failed")
    logger.debug(search_request)
    # 获取搜索结果
    try:
        search_result = await search_in_web(
            query=search_request.search_term,
            engine=engine
        )
    except Exception as e:
        logger.exception(f"Search In Web: {e} when getting search {prompt}")
        return HTTPException(status_code=405, detail="Search In Web Req Failed")
    # 构建返回消息
    message.reverse()
    message.append({"role": "system", "content": f"{SYSTEM_PROMPT}"})
    # ------------------------#
    message.append({"role": "system", "content": build_search_tips(search_result)})
    message.reverse()
    all_params.update({"messages": message})
    return all_params
