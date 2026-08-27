import os

import httpx


class AnalyzeError(Exception):
    """사용자에게 그대로 보여줄 분석 오류. status 에 HTTP 상태 코드를 담는다."""

    def __init__(self, status, message):

        super().__init__(message)
        self.status = status
        self.message = message


class ImageAnalyzer:

    MAX_BYTES = 5 * 1024 * 1024
    ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    TIMEOUT = 10
    DEFAULT_API_URL = "http://127.0.0.1:9000/analyze"

    def __init__(self, api_url=None, client=None):

        self.api_url = api_url or os.getenv("AI_API_URL", self.DEFAULT_API_URL)
        self.client = client

    def validate(self, content_type, data):

        if content_type not in self.ALLOWED_TYPES:
            raise AnalyzeError(415, "이미지 파일만 올릴 수 있어요")

        if len(data) > self.MAX_BYTES:
            raise AnalyzeError(413, "파일이 너무 큽니다 (5MB 이하)")

    async def analyze(self, filename, content_type, data):

        self.validate(content_type, data)

        if self.client is not None:
            return await self._request(self.client, filename, content_type, data)

        async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
            return await self._request(client, filename, content_type, data)

    async def _request(self, client, filename, content_type, data):

        try:
            response = await client.post(
                self.api_url, files={"file": (filename, data, content_type)}
            )
        except httpx.TimeoutException:
            raise AnalyzeError(504, "분석 서버 응답이 느려요")
        except httpx.ConnectError:
            raise AnalyzeError(502, "분석 서버에 연결할 수 없어요")
        except httpx.TransportError:
            raise AnalyzeError(502, "분석 서버와 통신하지 못했어요")

        if response.status_code != 200:
            raise AnalyzeError(502, f"분석 서버 오류 ({response.status_code})")

        try:
            return response.json()
        except ValueError:
            raise AnalyzeError(502, "분석 서버 응답을 이해할 수 없어요")
