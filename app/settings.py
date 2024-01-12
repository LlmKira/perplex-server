# -*- coding: utf-8 -*-
# @Time    : 2023/12/15 上午8:14
# @Author  : sudoskys
# @File    : settings.py


from dotenv import load_dotenv
from pydantic import ConfigDict, model_validator
from pydantic_settings import BaseSettings

load_dotenv()


class ServerSettings(BaseSettings):
    openai_base_url: str = "https://api.openai.com/v1"
    openai_api_key: str
    openai_model: str
    model_config = ConfigDict()

    @model_validator(mode="after")
    def check_env(self):
        if not self.openai_api_key or len(self.openai_api_key) < 4:
            raise ValueError("openai_api_key is not set or is too short")
        if self.openai_base_url.endswith("/"):
            self.openai_base_url = self.openai_base_url[:-1]
        return self


CurrentSetting = ServerSettings()
