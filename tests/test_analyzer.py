import httpx
import pytest

from vibe_coding import AnalyzeError, ImageAnalyzer


def make_analyzer(handler):
    """AI API 응답을 MockTransport 로 갈아끼운 분석기를 만든다"""
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return ImageAnalyzer(api_url="http://ai.test/analyze", client=client)


# ImageAnalyzer Tests
def test_validate():
    """허용된 이미지 타입과 크기는 검증을 통과하는 테스트"""
    analyzer = ImageAnalyzer()

    assert analyzer.validate("image/jpeg", b"binary") is None


def test_validate_rejects_non_image():
    """이미지가 아닌 타입은 415로 거부하는 테스트"""
    analyzer = ImageAnalyzer()

    with pytest.raises(AnalyzeError) as error:
        analyzer.validate("text/plain", b"binary")

    assert error.value.status == 415


def test_validate_rejects_oversized():
    """5MB를 넘으면 413으로 거부하는 테스트"""
    analyzer = ImageAnalyzer()
    data = b"x" * (ImageAnalyzer.MAX_BYTES + 1)

    with pytest.raises(AnalyzeError) as error:
        analyzer.validate("image/png", data)

    assert error.value.status == 413


def test_validate_allows_exact_max():
    """정확히 5MB는 통과하는 경계 테스트"""
    analyzer = ImageAnalyzer()
    data = b"x" * ImageAnalyzer.MAX_BYTES

    assert analyzer.validate("image/png", data) is None


@pytest.mark.asyncio
async def test_analyze():
    """AI API 의 JSON 응답을 그대로 돌려주는 테스트"""

    def handler(request):
        return httpx.Response(200, json={"message": "사진 잘 받았어요!"})

    analyzer = make_analyzer(handler)

    result = await analyzer.analyze("scrap.jpg", "image/jpeg", b"binary")

    assert result["message"] == "사진 잘 받았어요!"


@pytest.mark.asyncio
async def test_analyze_sends_file_field():
    """사진을 file 필드에 multipart 로 실어 보내는 테스트"""
    sent = {}

    def handler(request):
        sent["content_type"] = request.headers["content-type"]
        sent["body"] = request.content
        return httpx.Response(200, json={"message": "ok"})

    analyzer = make_analyzer(handler)

    await analyzer.analyze("scrap.jpg", "image/jpeg", b"binary")

    assert sent["content_type"].startswith("multipart/form-data")
    assert b'name="file"' in sent["body"]
    assert b"scrap.jpg" in sent["body"]


@pytest.mark.asyncio
async def test_analyze_maps_connect_error():
    """AI 서버에 연결하지 못하면 502로 바꾸는 테스트"""

    def handler(request):
        raise httpx.ConnectError("connection refused")

    analyzer = make_analyzer(handler)

    with pytest.raises(AnalyzeError) as error:
        await analyzer.analyze("scrap.jpg", "image/jpeg", b"binary")

    assert error.value.status == 502


@pytest.mark.asyncio
async def test_analyze_maps_timeout():
    """AI 서버 응답이 늦으면 504로 바꾸는 테스트"""

    def handler(request):
        raise httpx.ReadTimeout("too slow")

    analyzer = make_analyzer(handler)

    with pytest.raises(AnalyzeError) as error:
        await analyzer.analyze("scrap.jpg", "image/jpeg", b"binary")

    assert error.value.status == 504


@pytest.mark.asyncio
async def test_analyze_maps_error_status():
    """AI 서버가 200이 아니면 502로 바꾸는 테스트"""

    def handler(request):
        return httpx.Response(500, json={"detail": "boom"})

    analyzer = make_analyzer(handler)

    with pytest.raises(AnalyzeError) as error:
        await analyzer.analyze("scrap.jpg", "image/jpeg", b"binary")

    assert error.value.status == 502


@pytest.mark.asyncio
async def test_analyze_validates_before_calling():
    """검증에 실패하면 AI API 를 호출하지 않는 테스트"""
    called = []

    def handler(request):
        called.append(request)
        return httpx.Response(200, json={"message": "ok"})

    analyzer = make_analyzer(handler)

    with pytest.raises(AnalyzeError):
        await analyzer.analyze("memo.txt", "text/plain", b"binary")

    assert called == []


@pytest.mark.asyncio
async def test_analyze_maps_broken_json():
    """AI 서버가 JSON 이 아닌 응답을 주면 502로 바꾸는 테스트"""

    def handler(request):
        return httpx.Response(200, text="<html>not json</html>")

    analyzer = make_analyzer(handler)

    with pytest.raises(AnalyzeError) as error:
        await analyzer.analyze("scrap.jpg", "image/jpeg", b"binary")

    assert error.value.status == 502
