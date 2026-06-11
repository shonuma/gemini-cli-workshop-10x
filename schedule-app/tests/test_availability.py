import pytest

from models import ResponseModel


def test_availability_accepts_various_strings():
    """
    availabilityが任意の文字列を受け入れることを確認するテスト
    """
    # 従来の記号
    data1 = {
        "name": "User1",
        "availability": {"2026-05-11": "○", "2026-05-12": "△", "2026-05-13": "×"}
    }
    resp1 = ResponseModel.model_validate(data1)
    assert resp1.availability["2026-05-13"] == "×"

    # 特殊な記号や英数字
    data2 = {
        "name": "User2",
        "availability": {"2026-05-11": "◎", "2026-05-12": "x", "2026-05-13": "OK"}
    }
    resp2 = ResponseModel.model_validate(data2)
    assert resp2.availability["2026-05-11"] == "◎"
    assert resp2.availability["2026-05-12"] == "x"
    assert resp2.availability["2026-05-13"] == "OK"

    # コメント付きの回答
    data3 = {
        "name": "User3",
        "availability": {"2026-05-11": "○ (19時以降)"}
    }
    resp3 = ResponseModel.model_validate(data3)
    assert resp3.availability["2026-05-11"] == "○ (19時以降)"


if __name__ == "__main__":
    pytest.main([__file__])
