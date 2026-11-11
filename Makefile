PY ?= python3

.PHONY: ref ingest link entities hls wikidata site serve test
ref:
	$(PY) scripts/ref_places.py
ingest:
	$(PY) scripts/ingest_ab.py
	$(PY) scripts/ingest_ptt.py
	$(PY) scripts/enrich_ptt.py
link:
	$(PY) scripts/link_ptt_ab.py
	$(PY) scripts/measure_links.py
entities:
	$(PY) scripts/cluster.py
	$(PY) scripts/authority.py link
	$(PY) scripts/measure_clusters.py
hls:
	$(PY) scripts/hls_coverage.py
wikidata:
	$(PY) scripts/authority.py fetch
site:
	$(PY) scripts/build_site.py
	$(PY) scripts/build_pages.py
	$(PY) scripts/build_maps.py
	$(PY) scripts/build_entries.py
	$(PY) scripts/build_hls.py
serve: site
	cd site && python3 -m http.server 8000
test:
	$(PY) -m unittest discover -s tests -v
