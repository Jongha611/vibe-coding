from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse

from vibe_coding.fgvc_iron_scraps.analyzer import AnalyzeError, ImageAnalyzer

STATIC_DIR = Path(__file__).parent / "static"


def create_app(analyzer=None):
    """사진을 받아 AI API 에 넘기고 그 결과를 화면에 돌려주는 허브.

    analyzer 를 주입하면 AI API 를 실제로 띄우지 않고도 테스트할 수 있다.
    """

    app = FastAPI(title="고철 이미지 분석")
    analyzer = analyzer or ImageAnalyzer()

    @app.get("/")
    async def index():
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/analyze")
    async def analyze_page():
        return FileResponse(STATIC_DIR / "analyze.html")

    @app.post("/api/analyze")
    async def api_analyze(file: UploadFile):
        data = await file.read()

        try:
            return await analyzer.analyze(file.filename, file.content_type, data)
        except AnalyzeError as error:
            raise HTTPException(status_code=error.status, detail=error.message)

    return app


app = create_app()
