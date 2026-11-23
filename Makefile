PY ?= python3

.PHONY: ref ingest link entities wanderungen zuzuege infrastruktur durchdringung-bern check-wanderungen hls elites wikidata site serve test
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
wanderungen:
	$(PY) scripts/migration.py
zuzuege:
	$(PY) scripts/zuzuege.py
infrastruktur:
	$(PY) scripts/infrastruktur.py
# BERNHIST_SQLITE=<Dump> liest die Referenz neu aus BERNHIST; ohne rechnet ref_bernhist.py aus data/ref/bernhist/werte.csv
durchdringung-bern:
	$(PY) scripts/ref_bernhist.py
	$(PY) scripts/durchdringung_bern.py
check-wanderungen:
	$(PY) scripts/check_migration.py --upstream
hls:
	$(PY) scripts/hls_coverage.py
elites:
	$(PY) scripts/elites_suisses.py
	$(PY) scripts/elites_match.py
wikidata:
	$(PY) scripts/authority.py fetch
site:
	$(PY) scripts/build_site.py
	$(PY) scripts/build_pages.py
	$(PY) scripts/build_maps.py
	$(PY) scripts/build_entries.py
	$(PY) scripts/build_hls.py
	$(PY) scripts/migration.py site
	$(PY) scripts/zuzuege.py site
	$(PY) scripts/infrastruktur.py site
	$(PY) scripts/durchdringung_bern.py site
serve: site
	cd site && python3 -m http.server 8000
test:
	$(PY) -m unittest discover -s tests -v
