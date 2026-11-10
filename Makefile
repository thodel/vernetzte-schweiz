PY ?= python3

.PHONY: ingest site serve test
ingest:
	$(PY) scripts/ingest_ab.py
	$(PY) scripts/ingest_ptt.py
site:
	$(PY) scripts/build_site.py
serve: site
	cd site && python3 -m http.server 8000
test:
	$(PY) -m unittest discover -s tests -v
