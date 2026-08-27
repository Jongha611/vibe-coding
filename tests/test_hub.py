import httpx
from fastapi.testclient import TestClient

from vibe_coding import ImageAnalyzer
from vibe_coding.fgvc_iron_scraps.hub import create_app


def ok_handler(request):
    """더미 AI 가 정상 응답을 준 상황"""
    return httpx.Response(
        200, json={"message": "사진 잘 받았어요!", "filename": "scrap.jpg", "size": 6}
    )


def make_client(handler=ok_handler):
    """AI API 응답을 MockTransport 로 갈아끼운 허브 클라이언트를 만든다"""
    ai_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    analyzer = ImageAnalyzer(api_url="http://ai.test/analyze", client=ai_client)
    return TestClient(create_app(analyzer=analyzer))


def upload(client, name="scrap.jpg", data=b"binary", content_type="image/jpeg"):
    """허브에 사진 한 장을 올린다"""
    return client.post("/api/analyze", files={"file": (name, data, content_type)})


# 허브 화면 Tests
def test_index():
    """대문이 분석 화면으로 가는 링크를 담아 내려오는 테스트"""
    response = make_client().get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "/analyze" in response.text


def test_analyze_page():
    """업로드 화면이 HTML 로 내려오는 테스트"""
    response = make_client().get("/analyze")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


# 허브 API Tests
def test_api_analyze():
    """사진을 올리면 AI 응답을 그대로 돌려주는 테스트"""
    response = upload(make_client())

    assert response.status_code == 200
    assert response.json()["message"] == "사진 잘 받았어요!"


def test_api_analyze_rejects_non_image():
    """이미지가 아닌 파일은 415로 거부하는 테스트"""
    response = upload(make_client(), name="memo.txt", content_type="text/plain")

    assert response.status_code == 415
    assert response.json()["detail"] == "이미지 파일만 올릴 수 있어요"


def test_api_analyze_rejects_oversized():
    """5MB를 넘는 사진은 413으로 거부하는 테스트"""
    data = b"x" * (ImageAnalyzer.MAX_BYTES + 1)

    response = upload(make_client(), data=data)

    assert response.status_code == 413


def test_api_analyze_requires_file():
    """file 필드가 없으면 422로 거부하는 테스트"""
    response = make_client().post("/api/analyze")

    assert response.status_code == 422


def test_api_analyze_maps_connect_error():
    """AI 서버가 꺼져 있으면 502로 알려주는 테스트"""

    def handler(request):
        raise httpx.ConnectError("connection refused")

    response = upload(make_client(handler))

    assert response.status_code == 502
    assert response.json()["detail"] == "분석 서버에 연결할 수 없어요"


def test_api_analyze_maps_timeout():
    """AI 서버 응답이 늦으면 504로 알려주는 테스트"""

    def handler(request):
        raise httpx.ReadTimeout("too slow")

    response = upload(make_client(handler))

    assert response.status_code == 504
