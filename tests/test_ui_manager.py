import core.ui_manager as ui_manager_module
from core.ui_manager import UIManager


class FakeApp:
    """Minimal stand-in for the Textual app, without any mounted widgets."""

    current_group = "6.1"

    def query_one(self, *_args, **_kwargs):
        raise LookupError("no widgets mounted")


def _record_notifications(monkeypatch, enabled: bool) -> list[tuple[str, str]]:
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(ui_manager_module, "desktop_notifications_enabled", lambda: enabled)
    monkeypatch.setattr(ui_manager_module, "send_desktop_notification", lambda title, msg: calls.append((title, msg)))
    return calls


def test_desktop_notification_is_sent_when_enabled(monkeypatch):
    calls = _record_notifications(monkeypatch, enabled=True)

    UIManager(FakeApp()).show_notification("Світло з'явиться о 14:00")

    assert calls == [("Svitlo CLI (Група 6.1)", "Світло з'явиться о 14:00")]


def test_desktop_notification_is_skipped_when_disabled(monkeypatch):
    calls = _record_notifications(monkeypatch, enabled=False)

    UIManager(FakeApp()).show_notification("Світло з'явиться о 14:00")

    assert calls == []
