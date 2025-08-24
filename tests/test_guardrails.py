import re

def test_language_no_promises():
    text = "This strategy guarantees a 10% monthly return."
    assert not re.search(r"guarantee", text, re.I), "Avoid 'guarantee' wording in outputs"

def test_stub():
    assert True
