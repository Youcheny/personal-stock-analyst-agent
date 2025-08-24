.PHONY: venv install memo screen

venv:
	python3 -m venv .venv

install: venv
	. .venv/bin/activate && pip install -r requirements.txt

memo:
	. .venv/bin/activate && python3 src/app.py memo $(TICKER)

screen:
	. .venv/bin/activate && python3 src/app.py screen --universe $(UNIVERSE) --min_fcf_yield $(FCF) --min_roic $(ROIC)
