"""
单元测试：AudioOverlayMixin._probe_clip_duration — 时长探测三级兜底（Issue #54）。

背景：Docker 镜像仅暴露 imageio-ffmpeg 自带的 ffmpeg，不含 ffprobe，
resolve_binary("ffprobe") 返回 None。此前 composite_anchor_video 直接把 None
塞进 subprocess.run([...])，触发 os.path.dirname(None) →
TypeError: expected str, bytes or os.PathLike object, not NoneType，
导致数字人任务在“视频拼接合成”步骤恒定失败且重试无法自愈。

覆盖：
- ffprobe 缺失但 ffmpeg 可用 → 从 ffmpeg -i 的 stderr Duration 行解析；
- ffprobe 与 ffmpeg 均缺失 → 返回 default，且不抛 TypeError；
- ffprobe 可用 → 使用 ffprobe stdout；
- 关键回归护栏：ffprobe 为 None 时，绝不以 None 作为可执行文件调用 subprocess.run。
"""

import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

import core.compositor.concatenator.audio_overlay as ao


CLIP = "/tmp/does_not_matter.mp4"


def _fake_run_factory(stderr="", stdout="", captured=None):
    """构造一个假的 subprocess.run，记录被调用时的可执行文件（argv[0]）。"""

    def _run(cmd, *args, **kwargs):
        if captured is not None:
            captured.append(cmd[0] if cmd else None)
        # 复现真实 subprocess 行为：argv[0] 为 None 时会抛 TypeError
        if cmd and cmd[0] is None:
            raise TypeError(
                "expected str, bytes or os.PathLike object, not NoneType"
            )
        return types.SimpleNamespace(
            returncode=0, stdout=stdout, stderr=stderr,
        )

    return _run


def _patch_resolve(monkeypatch, mapping):
    def _resolve(name):
        return mapping.get(name)
    monkeypatch.setattr(ao, "resolve_binary", _resolve)


def test_ffprobe_missing_uses_ffmpeg_fallback(monkeypatch):
    """ffprobe=None、ffmpeg 可用 → 从 ffmpeg stderr 的 Duration 行解析时长。"""
    _patch_resolve(monkeypatch, {"ffprobe": None, "ffmpeg": "/usr/local/bin/ffmpeg"})
    captured = []
    monkeypatch.setattr(
        ao.subprocess, "run",
        _fake_run_factory(
            stderr="Input #0, mov,mp4:\n  Duration: 00:00:03.20, start: 0.000000\n",
            captured=captured,
        ),
    )

    dur = ao.AudioOverlayMixin._probe_clip_duration(CLIP, default=5.0)

    assert dur == pytest.approx(3.2, abs=0.01)
    # 护栏：从未以 None 作为可执行文件调用 subprocess.run
    assert None not in captured


def test_both_missing_returns_default_no_typeerror(monkeypatch):
    """ffprobe 与 ffmpeg 均为 None → 返回 default，不抛 TypeError。"""
    _patch_resolve(monkeypatch, {"ffprobe": None, "ffmpeg": None})
    captured = []
    monkeypatch.setattr(ao.subprocess, "run", _fake_run_factory(captured=captured))

    dur = ao.AudioOverlayMixin._probe_clip_duration(CLIP, default=5.0)

    assert dur == 5.0
    # 两者皆 None 时不应发起任何 subprocess 调用
    assert captured == []


def test_ffprobe_present_uses_ffprobe(monkeypatch):
    """ffprobe 可用 → 直接用 ffprobe 的 stdout。"""
    _patch_resolve(monkeypatch, {"ffprobe": "/usr/bin/ffprobe", "ffmpeg": "/usr/bin/ffmpeg"})
    captured = []
    monkeypatch.setattr(
        ao.subprocess, "run",
        _fake_run_factory(stdout="4.500000\n", captured=captured),
    )

    dur = ao.AudioOverlayMixin._probe_clip_duration(CLIP, default=5.0)

    assert dur == pytest.approx(4.5, abs=0.01)
    assert captured[0] == "/usr/bin/ffprobe"


def test_ffprobe_raises_falls_through_to_ffmpeg(monkeypatch):
    """ffprobe 调用异常 → 继续走 ffmpeg 兜底而非崩溃。"""
    _patch_resolve(monkeypatch, {"ffprobe": "/usr/bin/ffprobe", "ffmpeg": "/usr/bin/ffmpeg"})

    calls = {"n": 0}

    def _run(cmd, *args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:  # 第一次是 ffprobe
            raise OSError("probe boom")
        return types.SimpleNamespace(
            returncode=0,
            stdout="",
            stderr="  Duration: 00:00:02.00, start: 0.000000\n",
        )

    monkeypatch.setattr(ao.subprocess, "run", _run)

    dur = ao.AudioOverlayMixin._probe_clip_duration(CLIP, default=5.0)

    assert dur == pytest.approx(2.0, abs=0.01)
