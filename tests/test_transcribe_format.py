from anki_pipeline.transcribe import fmt_timestamp, render_transcripts


def test_fmt_timestamp():
    assert fmt_timestamp(0) == "00:00"
    assert fmt_timestamp(75.9) == "01:15"
    assert fmt_timestamp(3725) == "1:02:05"


def test_render_transcripts():
    rows = [(0.0, 2.0, "Hello there."), (65.2, 70.0, "How are you?")]
    clean, stamped = render_transcripts(rows)
    assert clean == "Hello there.\nHow are you?\n"
    assert stamped == "[00:00] Hello there.\n[01:05] How are you?\n"
