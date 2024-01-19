# -*- coding: utf-8 -*-
# @Time    : 2024/1/11 下午11:07
# @File    : search.py
# @Software: PyCharm
import json
from typing import List

import requests
from googleapiclient.discovery import build
from loguru import logger
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from tavily import TavilyClient


class SearchEngine(BaseModel):
    api_key: str

    def search(self, search_term: str):
        raise NotImplementedError


class BuildError(Exception):
    pass


class SearchEngineResult(BaseModel):
    title: str
    link: str
    snippet: str


class GoogleSearchEngine(SearchEngine):
    api_key: str
    cse_id: str

    async def search(self, search_term: str) -> List[SearchEngineResult]:
        service = build("customsearch", "v1", developerKey=self.api_key)
        res = service.cse().list(q=search_term, cx=self.cse_id).execute()
        if 'items' not in res:
            logger.info("No Result")
            return []
        item_list = res['items']
        logger.debug(f"Got {len(item_list)} results")
        _result = []
        for item in item_list:
            _result.append(
                SearchEngineResult(
                    title=item.get("title", "Undefined"),
                    link=item.get("link", "Undefined"),
                    snippet=item.get("snippet", "Undefined")
                )
            )

        _result = _result[:5]
        return _result


class TavilySearchEngine(SearchEngine):
    api_key: str

    @property
    def client(self):
        return TavilyClient(api_key=self.api_key)

    async def search(self, search_term: str) -> List[SearchEngineResult]:
        assert isinstance(search_term, str), f"search_term should be a str, but got {type(search_term)}"
        search_term = search_term + " ?"
        response = self.client.search(query=search_term, search_depth="basic")
        context = [obj for obj in response.get("results", [])]
        _result = []
        logger.debug(f"Got {len(context)} results")
        for item in context:
            _result.append(
                SearchEngineResult(
                    title=item.get("title", "Undefined"),
                    link=item.get("url", "Undefined"),
                    snippet=item.get("content", "Undefined")
                )
            )
        _result = _result[:5]
        return _result


class SerperSearchEngine(SearchEngine):
    api_key: str

    async def search(self, search_term: str) -> List[SearchEngineResult]:
        url = "https://google.serper.dev/search"
        payload = json.dumps({
            "q": search_term,
        })
        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        result_list = response.json()["organic"]
        _result = []
        logger.debug(f"Got {len(result_list)} results")
        for item in result_list:
            _result.append(
                SearchEngineResult(
                    title=item.get("title", "Undefined"),
                    link=item.get("link", "Undefined"),
                    snippet=item.get("snippet", "Undefined")
                )
            )
        _result = _result[:4]
        return _result


class SearchEngineManager(BaseSettings):
    google_api_key: str
    google_cse_id: str
    tavily_api_key: str
    serper_api_key: str

    def build(self, engine: str, **kwargs):
        if engine == "google":
            if not self.google_api_key or not self.google_cse_id:
                raise BuildError("google_api_key or google_cse_id is not set")
            return GoogleSearchEngine(api_key=self.google_api_key, cse_id=self.google_cse_id)
        if engine == "tavily":
            if not self.tavily_api_key:
                raise BuildError("tavily_api_key is not set")
            return TavilySearchEngine(api_key=self.tavily_api_key)
        if engine == "serper":
            if not self.serper_api_key:
                raise BuildError("serper_api_key is not set")
            return SerperSearchEngine(api_key=self.serper_api_key)
        raise BuildError(f"Engine {engine} not implemented, please select from google, tavily")

    def warn_check(self):
        # 检查是否有空的参数
        for key, value in self.model_dump().items():
            if not value:
                logger.warning(f"Empty {key} in SearchEngineManager")

    async def search(self, engine: str, search_term: str, **kwargs):
        return await self.build(engine, **kwargs).search(search_term=search_term)
