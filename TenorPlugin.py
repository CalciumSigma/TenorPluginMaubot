from ast import parse
from typing import Type
from bs4 import BeautifulSoup
import urllib.parse, re, json
from urllib import request
from urllib.request import urlopen
import urllib.error
from mautrix.types import ImageInfo, EventType, MessageType
from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper
from maubot import Plugin, MessageEvent
from maubot.handlers import event

tenor_pattern = re.compile(r"(?:https?:\/\/)?(?:www\.)?(?:tenor\.com\/view)(\S+)?")


class Config(BaseProxyConfig):
    def do_update(self, helper: ConfigUpdateHelper) -> None:
        helper.copy("appid")
        helper.copy("source")
        helper.copy("response_type")


class TenorImagePlugin(Plugin):
    async def start(self) -> None:
        await super().start()

    @classmethod
    def get_config_class(cls) -> Type[BaseProxyConfig]:
        return Config

    @event.on(EventType.ROOM_MESSAGE)
    async def on_message(self, evt: MessageEvent) -> None:
        if evt.content.msgtype != MessageType.TEXT or evt.content.body.startswith("!"):
            return
        for url_tup in tenor_pattern.findall(evt.content.body):
            await evt.mark_read()

            url = "https://tenor.com/view" + ''.join(url_tup)

            self.log.warning(f"link {url} ")

            html = urlopen(url).read()
            soup = BeautifulSoup(html)
            image_url = soup.find('link', {'rel': 'image_src'}).get('href')
            response = await self.http.get(image_url)
            if response.status != 200:
                self.log.warning(f"Unexpected status fetching image {image_url}: {response.status}")
                return None
            thumbnail = await response.read()
            filename = url_tup + ".gif"
            uri = await self.client.upload_media(thumbnail, mime_type='image/gif', filename=filename)
            await self.client.send_image(evt.room_id, url=uri, file_name=filename, info=ImageInfo(
                mimetype='image/gif'
            ))
