PY ?= python3

.PHONY: ref ingest site serve test
ref:
	$(PY) scripts/ref_places.py
ingest:
	$(PY) scripts/ingest_ab.py
	$(PY) scripts/ingest_ptt.py
	$(PY) scripts/enrich_ptt.py
site:
	$(PY) scripts/build_site.py
serve: site
	cd site && python3 -m http.server 8000
test:
	$(PY) -m unittest discover -s tests -v
