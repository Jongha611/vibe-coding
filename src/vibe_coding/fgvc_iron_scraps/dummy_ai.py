from fastapi import FastAPI, UploadFile


def create_app():
    """진짜 고철 분석 AI 가 생기기 전까지 그 자리를 대신하는 더미 서버.

    허브에 목 라우트를 섞지 않으려고 별도 프로세스로 띄운다.
    진짜 API 가 생기면 이 파일과 tests/test_dummy_ai.py 를 지운다.
    """

    app = FastAPI(title="더미 고철 분석 AI")

    @app.post("/analyze")
    async def analyze(file: UploadFile):
        data = await file.read()

        return {
            "message": "사진 잘 받았어요!",
            "filename": file.filename,
            "size": len(data),
        }

    return app


app = create_app()
