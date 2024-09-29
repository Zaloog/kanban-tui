run := uv run

.PHONY: test
test:
	$(run) pytest $(ARGS)

.PHONY: seed
seed:
	$(run) python tools/seed.py
