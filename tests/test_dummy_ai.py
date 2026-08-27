from fastapi.testclient import TestClient

from vibe_coding.fgvc_iron_scraps.dummy_ai import create_app


def upload(client, name="scrap.jpg", data=b"binary", content_type="image/jpeg"):
    """더미 AI 에 사진 한 장을 올린다"""
    return client.post("/analyze", files={"file": (name, data, content_type)})


# 더미 AI Tests
def test_analyze():
    """사진을 받으면 잘 받았다는 메시지를 돌려주는 테스트"""
    client = TestClient(create_app())

    response = upload(client)

    assert response.status_code == 200
    assert response.json()["message"] == "사진 잘 받았어요!"


def test_analyze_echoes_file_info():
    """파일 이름과 바이트 크기를 함께 돌려주는 테스트"""
    client = TestClient(create_app())

    response = upload(client, name="iron.png", data=b"0123456789")

    body = response.json()
    assert body["filename"] == "iron.png"
    assert body["size"] == 10


def test_analyze_requires_file():
    """file 필드가 없으면 422로 거부하는 테스트"""
    client = TestClient(create_app())

    response = client.post("/analyze")

    assert response.status_code == 422
