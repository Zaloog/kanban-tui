.PHONY: all
MAKE               := make --no-print-directory
RUN 			   := uv run
VERSION            := v$(shell uv version --short)


# -- Testing ---
test:
	$(RUN) pytest $(ARGS) --no-cov

check:
	$(RUN) ruff check . $(ARGS)
	$(RUN) mypy . $(ARGS)

# -- Run in Dev mode ---
dev:
	$(RUN) textual run -c kanban-tui --dev

# -- Run in Dev demo mode ---
devd:
	$(RUN) textual run -c kanban-tui demo --dev

release:
	git tag $(VERSION)
	git push origin $(VERSION)

notes:
	# Thanks Will
	gh release create --generate-notes $(VERSION)

# -- Jira locally ---
ju:
	docker compose up -d

jd:
	docker compose down
