from vibe_coding import main


# vibe_coding Package Tests
def test_main_prints_entry_point(capsys):
    """콘솔 스크립트 진입점이 자기 식별 문자열을 출력하는 테스트"""
    main()

    assert capsys.readouterr().out == "vibe-coding = vibe_coding:main\n"
