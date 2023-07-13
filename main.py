import aiohttp
import asyncio
import json
import uuid
from loguru import logger


class ClaudeWeb:
    def __init__(self, url, session_token, proxy):
        self.session_token: str = session_token
        self.proxy: str = proxy
        self.url: str = url or "https://claude.ai"
        self.session = aiohttp.ClientSession()

    def __del__(self):
        asyncio.run(self.session.close())

    async def ask_with_stream(self, organization_uuid, conversation_uuid, message):
        """向 Claude AI 发送消息"""
        request_url = f"{self.url}/api/append_message"
        headers = self._get_headers()
        payload = self._get_payload(organization_uuid, conversation_uuid, message)
        try:
            async with self.session.post(request_url, headers=headers, json=payload, proxy=self.proxy) as resp:
                async for line in resp.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data:'):
                        data_json = json.loads(line[5:])
                        yield data_json['completion']
        except Exception as e:
            logger.error(f"An error occurred in ask_with_stream: {e}")
            raise

    async def create_session(self, organization_uuid, name: str = "AI assistant discussion"):
        """创建一个会话"""
        request_url = f'{self.url}/api/organizations/{organization_uuid}/chat_conversations'
        headers = self._get_headers()
        session_uuid = str(uuid.uuid4())
        payload = {"uuid": session_uuid, "name": name}
        try:
            async with self.session.post(request_url, headers=headers, json=payload, proxy=self.proxy) as resp:
                data = await resp.text()
                data_json = json.loads(data)
                print(data_json)
                return session_uuid
        except Exception as e:
            logger.error(f"An error occurred in create_session: {e}")
            raise

    async def get_conversation(self, organization_uuid, conversation_uuid):
        """获得某个会话的所有消息"""
        request_url = f'{self.url}/api/organizations/{organization_uuid}/chat_conversations/{conversation_uuid}'
        headers = self._get_headers()
        try:
            async with self.session.get(request_url, headers=headers, proxy=self.proxy) as resp:
                data = await resp.text()
                data_json = json.loads(data)
                return data_json
        except Exception as e:
            logger.error(f"An error occurred in get_conversation: {e}")
            raise

    async def get_session(self, organization_uuid):
        """获得用户的所有会话"""
        request_url = f'{self.url}/api/organizations/{organization_uuid}/chat_conversations'
        headers = self._get_headers()
        try:
            async with self.session.get(request_url, headers=headers, proxy=self.proxy) as resp:
                data = await resp.text()
                data_json = json.loads(data)
                session_uuids = [session['uuid'] for session in data_json]
                return session_uuids
        except Exception as e:
            logger.error(f"An error occurred in get_session: {e}")
            raise

    async def get_uuid(self):
        """获得用户的uuid"""
        request_url = f'{self.url}/api/organizations'
        headers = self._get_headers()
        try:
            async with self.session.get(request_url, headers=headers, proxy=self.proxy) as resp:
                data = await resp.text()
                data_json = json.loads(data)
                organization_uuid = data_json[0]["uuid"]
                return organization_uuid
        except Exception as e:
            logger.error(f"An error occurred in get_uuid: {e}")
            raise

    def _get_headers(self):
        return {"Cookie": self.session_token,
                "Content-Type": "application/json",
                "Accept": "text/event-stream",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79",
                }

    def _get_payload(self, organization_uuid, conversation_uuid, message, model: str = "claude-2"):
        return {
            "completion": {
                "prompt": message,
                "timezone": "America/Los_Angeles",
                "model": model
            },
            "organization_uuid": organization_uuid,
            "conversation_uuid": conversation_uuid,
            "text": message,
            "attachments": []
        }

    async def main(self):
        """测试函数"""
        # 获得用户的uuid
        organization_uuid = await self.get_uuid()

        # 获得用户的所有会话
        await self.get_session(organization_uuid)

        # 创建一个会话
        conversation_uuid = self.create_session(organization_uuid)

        # 获得某个会话的所有消息
        await self.get_conversation(organization_uuid, conversation_uuid)

        # 向Claude AI发送消息
        # message = "hello"
        # async for completion in self.ask_with_stream(organization_uuid, conversation_uuid, message):
        #     logger.debug(completion)


if __name__ == "__main__":
    """使用例子"""
    session_token = "xxxxxx"  # 您的会话令牌
    proxy = None  # 您的代理
    claude = ClaudeWeb(None, session_token, proxy)
    asyncio.run(claude.main())
