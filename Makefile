.PHONY: all
MAKE               := make --no-print-directory
RUN 			   := uv run


# -- Testing ---
test:
	$(RUN) pytest $(ARGS)

check:
	$(RUN) ruff check . $(ARGS)
	$(RUN) mypy . $(ARGS)

# -- Run in Dev mode ---
dev:
	$(RUN) textual run -c kanban-tui demo --dev


# -- Jira locally ---
ju:
	docker compose up -d

jd:
	docker compose down
