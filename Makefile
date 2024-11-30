MAKE               := make --no-print-directory
RUN 			   := uv run

DESCRIBE           := $(shell git describe --match "v*" --always --tags)
DESCRIBE_PARTS     := $(subst -, ,$(DESCRIBE))

VERSION_TAG        := $(word 1,$(DESCRIBE_PARTS))
COMMITS_SINCE_TAG  := $(word 2,$(DESCRIBE_PARTS))

VERSION            := $(subst v,,$(VERSION_TAG))
VERSION_PARTS      := $(subst ., ,$(VERSION))

MAJOR              := $(word 1,$(VERSION_PARTS))
MINOR              := $(word 2,$(VERSION_PARTS))
MICRO              := $(word 3,$(VERSION_PARTS))

NEXT_MAJOR         := $(shell echo $$(($(MAJOR)+1)))
NEXT_MINOR         := $(shell echo $$(($(MINOR)+1)))
NEXT_MICRO         := $(shell echo $$(($(MICRO)+1)))

# most of it found here
# https://gist.github.com/grihabor/4a750b9d82c9aa55d5276bd5503829be
# -- Increment Tags ---
.PHONY: micro
micro:
	@echo "v$(MAJOR).$(MINOR).$(NEXT_MICRO)"
	# git tag "v$(MAJOR).$(MINOR).$(NEXT_MICRO)"

.PHONY: minor
minor:
	@echo "v$(MAJOR).$(NEXT_MINOR).0"
	# git tag  "v$(MAJOR).$(NEXT_MINOR).0"

.PHONY: major
major:
	@echo "v$(NEXT_MAJOR).0.0"
	# git tag  "v$(NEXT_MAJOR).0.0"


# -- Testing ---
.PHONY: test
test:
	$(RUN) pytest $(ARGS)

#.PHONY: seed
#seed:
#	$(run) python tools/seed.py
