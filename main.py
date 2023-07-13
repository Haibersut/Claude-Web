import aiohttp
import asyncio
import json
import uuid
import mimetypes
from loguru import logger


class ClaudeWeb:
    def __init__(self, url, session_token, proxy, timeout=60):
        self.session_token: str = session_token
        self.proxy: str = proxy
        self.url: str = url or "https://claude.ai"
        self.timeout: int = timeout
        self.sessions = {}

    async def ask_with_stream(self, organization_uuid, conversation_uuid, message):
        """向 Claude AI 发送消息"""
        request_url = f"{self.url}/api/append_message"
        headers = self._get_headers()
        payload = self._get_payload(organization_uuid, conversation_uuid, message)
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(request_url, headers=headers, json=payload, proxy=self.proxy) as resp:
                    completion_text: str = ''
                    async for line in resp.content:
                        try:
                            line = line.decode('utf-8').strip()
                            if not line.startswith("data:"):
                                continue
                            line = line[len("data:"):]
                            if not line:
                                continue
                            data_json = json.loads(line)
                        except json.JSONDecodeError:
                            raise Exception(f"JSON解码错误: {line}") from None
                        completion_text = data_json['completion']
                        if data_json.get('stop_reason') == 'stop_sequence':
                            break
                        yield data_json['completion']
            logger.debug(f"[Claude] 完整回复内容 - {completion_text}")
        except Exception as e:
            logger.error(f"An error occurred in ask_with_stream: {e}")
            raise

    async def create_session(self, organization_uuid, name: str = "AI assistant discussion"):
        """创建一个会话"""
        request_url = f'{self.url}/api/organizations/{organization_uuid}/chat_conversations'
        headers = self._get_headers()
        session_uuid = str(uuid.uuid4())
        self.sessions[len(self.sessions) + 1] = session_uuid
        payload = {"uuid": session_uuid, "name": name}
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(request_url, headers=headers, json=payload, proxy=self.proxy) as resp:
                    data = await resp.text()
                    data_json = json.loads(data)
                    logger.debug(data_json)
            return session_uuid
        except Exception as e:
            logger.error(f"An error occurred in create_session: {e}")
            raise

    async def get_conversation(self, organization_uuid, conversation_uuid):
        """获得某个会话的所有消息"""
        request_url = f'{self.url}/api/organizations/{organization_uuid}/chat_conversations/{conversation_uuid}'
        headers = self._get_headers()
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(request_url, headers=headers, proxy=self.proxy) as resp:
                    data = await resp.text()
                    data_json = json.loads(data)
                    return data_json
        except Exception as e:
            logger.error(f"An error occurred in get_conversation: {e}")
            raise

    async def convert_file(self, file_content, file_name):
        """文件格式化，还用不了（"""

        request_url = f'{self.url}/api/convert_document'
        headers = {
            "Cookie": self.session_token,
            "Accept": "text/event-stream",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79",
        }

        mime_type = mimetypes.guess_type(file_name)[0]

        if mime_type not in ['application/pdf', 'text/csv', 'text/plain']:
            raise ValueError(
                f"不支持的文件类型: {mime_type}. 只支持pdf, csv和txt文件")
        data = aiohttp.FormData()
        data.add_field('file', file_content, filename=file_name, content_type=mime_type)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(request_url, headers=headers, data=data, proxy=self.proxy) as response:
                    print(response)

        except Exception as e:
            logger.error(f"An error occurred in convert_file: {e}")
            raise

    async def get_session(self, organization_uuid):
        """获得用户的所有会话"""
        request_url = f'{self.url}/api/organizations/{organization_uuid}/chat_conversations'
        headers = self._get_headers()
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(request_url, headers=headers, proxy=self.proxy) as resp:
                    data = await resp.text()
                    data_json = json.loads(data)
                    session_uuids = [session['uuid'] for session in data_json]
                    return session_uuids
        except Exception as e:
            logger.error(f"An error occurred in get_session: {e}")
            raise

    async def get_uuid(self):
        """获得用户的 UUID"""
        request_url = f'{self.url}/api/organizations'
        headers = self._get_headers()
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(request_url, headers=headers, proxy=self.proxy) as resp:
                    data = await resp.text()
                    data_json = json.loads(data)
                    organization_uuid = data_json[0]["uuid"]
                    return organization_uuid
        except Exception as e:
            logger.error(f"An error occurred in get_uuid: {e}")
            raise

    def get_session_by_id(self, id):
        """根据编号获取会话的 UUID"""
        return self.sessions.get(id)

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
        # organization_uuid = await self.get_uuid()

        # 获得用户的所有会话
        # await self.get_session(organization_uuid)

        # 创建一个会话
        # conversation_uuid = await self.create_session(organization_uuid)

        # 获得某个会话的所有消息
        # await self.get_conversation(organization_uuid, conversation_uuid)

        # 向Claude AI发送消息
        # message = "hello"
        # async for completion in self.ask_with_stream(organization_uuid, conversation_uuid, message):
            # logger.debug(completion)

        # 文件转换，有bug
        # with open("test.pdf", "rb") as file_content:
            # await self.convert_file(file_content, "test.pdf")


if __name__ == "__main__":
    """使用例子"""
    session_token = "xxxxx"  # 您的会话令牌
    proxy = None  # 您的代理
    claude = ClaudeWeb(None, session_token, proxy)
    asyncio.run(claude.main())
