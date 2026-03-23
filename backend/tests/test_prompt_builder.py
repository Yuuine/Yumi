"""prompt_builder 消息数组规范化与不变量测试。"""

from backend.services.prompt_builder import (
    finalize_history_and_current_message,
    _verify_messages_invariants,
)


def test_finalize_empty_history():
    pairs, final = finalize_history_and_current_message([], "当前问题")
    assert pairs == []
    assert final == "当前问题"


def test_finalize_merge_trailing_user_with_current():
    pairs, final = finalize_history_and_current_message(
        [{"role": "user", "content": "前半"}],
        "后半",
    )
    assert pairs == []
    assert final == "前半\n\n后半"


def test_finalize_drop_leading_assistant():
    pairs, final = finalize_history_and_current_message(
        [
            {"role": "assistant", "content": "孤儿"},
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "嗨"},
        ],
        "新问题",
    )
    assert pairs == [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "嗨"},
    ]
    assert final == "新问题"


def test_finalize_merge_consecutive_user():
    pairs, final = finalize_history_and_current_message(
        [
            {"role": "user", "content": "a"},
            {"role": "user", "content": "b"},
            {"role": "assistant", "content": "ok"},
        ],
        "next",
    )
    assert pairs == [
        {"role": "user", "content": "a\n\nb"},
        {"role": "assistant", "content": "ok"},
    ]
    assert final == "next"


def test_verify_invariants_valid():
    msgs = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "u1"},
        {"role": "assistant", "content": "a1"},
        {"role": "user", "content": "u2"},
    ]
    _verify_messages_invariants(msgs)


def test_verify_rejects_second_system():
    try:
        _verify_messages_invariants(
            [
                {"role": "system", "content": "a"},
                {"role": "user", "content": "u"},
                {"role": "system", "content": "bad"},
            ]
        )
    except ValueError as e:
        assert "system" in str(e).lower()
    else:
        raise AssertionError("expected ValueError")
