# -*- coding: utf-8 -*-
# @Time    : 2023/12/15 上午1:26
# @Author  : sudoskys
# @File    : __init__.py.py
from pprint import pprint

import requests
from fastapi import FastAPI, Request, HTTPException
from loguru import logger
from tenacity import retry, wait_random_exponential, stop_after_attempt

from app.settings import CurrentSetting

OPENAI_API_KEY = CurrentSetting.openai_api_key
OPENAI_BASE_URL = CurrentSetting.openai_base_url
OPENAI_MODEL = CurrentSetting.openai_model

SYSTEM_PROMPT = """
1. 每句话需要添加来源，格式为：“上标数字”。 例如：[¹](https://examplelink1.com/)。
2. 来源链接不能放在回答末尾。
3. 建议优先使用在线数据。
4. 来源标记只能是在线数据的链接。
5. 您的回答应避免给出过时、不存在或虚假的内容或不正确的语法。
同时，这里有一些搜索的示例：
用户：皇马对阵切尔西
系统：<!--<隐藏在线数据>--> 
您好！👋 我是 GPT5。根据从网上数据中找到的信息，皇家马德里在2022/2023赛季欧洲冠军联赛四分之一决赛首回合于2023年4月12日在圣地亚哥伯纳乌举行了与切尔西的比赛¹ (https://theathletic.com/live-blogs/real-madrid-chelsea-champions-league-live-scores-updates-result/uVCAEHzxwQa9/)。两场比赛中，皇马以2-0的比分获胜，本泽马和阿森西奥均打入一球² (https://www.sportingnews.com/us/soccer/news/real-madrid-vs-chelsea-live-score-highlights-champions-league/ocvgfhg2jhsvtdhh9nbfhx7m)。在第74分钟，阿森西奥在左路完成一个漂亮的进球，为皇马锁定了胜利³ (https://www.theguardian.com/football/live/2023/apr/12/real-madrid-v-chelsea-champions-league-quarter-final-first-leg-live-score-updates)。据欧足联技术观察员小组称， 文森特-朱尼奥是比赛的最佳球员⁴ (https://www.independent.co.uk/sport/football/real-madrid-chelsea-live-stream-score-result-b2318505.html)。
<!--<Rule End>-->
"""
TOOLS = [{
    'name': 'search_in_google',
    'description': 'Get info on google.com to answer questions more accurately',
    'parameters': {
        'type': 'object',
        'properties': {
            'query': {
                'type': 'string',
                'description': 'the question entered in the search box.'
            },
            'search_term': {
                'type': 'string',
                'description': 'the search term entered in the search box.'
            },
        },
        'required': [
            'query'
        ]
    }
}]


# 获取 search 的patch后，我们请求数据，然后获取需要的搜索词，然后转变为system消息放回原请求
@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
def get_search_request(messages, force: bool = False, model=OPENAI_MODEL):
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + OPENAI_API_KEY,
    }
    json_data = {"model": model, "messages": messages}
    json_data.update({"tools": TOOLS})
    # if tool_choice is not None:
    #    json_data.update({"tool_choice": tool_choice})
    try:
        response = requests.post(
            f"{OPENAI_BASE_URL}/chat/completions",
            headers=headers,
            json=json_data,
        )
        return response
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        logger.exception(e)
        return e


class ValidationError(Exception):
    pass


app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Server Running"}


@app.post("/v1/chat/completions")
async def forward_request(request: Request):
    # 获取请求的全部参数
    all_params = await request.json()
    # 修改参数
    pprint(all_params)
    message = all_params.get("messages", None)
    if not isinstance(message, list) or len(message) == 0:
        return HTTPException(status_code=400, detail="Invalid Message Parameter")

    # 转发请求
    return all_params
