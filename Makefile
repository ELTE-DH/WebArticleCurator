.DEFAULT_GOAL = all
# Bash is needed for time, compgen, [[ and other builtin commands
SHELL := /bin/bash -o pipefail
RED := $(shell tput setaf 1)
GREEN := $(shell tput setaf 2)
NOCOLOR := $(shell tput sgr0)
PYTHON := python3

# Module specific parameters
MODULE := webarticlecurator

# These targets do not show as possible target with bash completion
__extra-deps:
	@# Do extra stuff (e.g. compiling, downloading) before building the package
	@exit 0
.PHONY: __extra-deps

__clean-extra-deps:
	@# e.g. @rm -rf stuff
	@exit 0
.PHONY: __clean-extra-deps

# From here only generic parts

all: clean venv install test
	@echo "all: clean, venv, install, test"
.PHONY: all

install-dep-packages:
	@echo "Installing needed packages from Aptfile..."
	@command -v apt-get >/dev/null 2>&1 || \
			(echo >&2 "$(RED)Command 'apt-get' could not be found!$(NOCOLOR)"; exit 1)
	@# Aptfile can be omited if empty
	@[[ ! -f "$(CURDIR)/Aptfile" ]] || \
	    ([[ $$(dpkg -l | grep -wcf $(CURDIR)/Aptfile) -eq $$(cat $(CURDIR)/Aptfile | wc -l) ]] || \
		(sudo -E apt-get update && \
		sudo -E apt-get -yq --no-install-suggests --no-install-recommends $(travis_apt_get_options) install \
			`cat $(CURDIR)/Aptfile`))
	@echo "$(GREEN)Needed packages are succesfully installed!$(NOCOLOR)"
.PHONY: install-dep-packages

venv:
	@poetry install --no-root
.PHONY: venv

build: install-dep-packages venv __extra-deps
	@poetry build
.PHONY: build

# Install the actual wheel package to test it in later steps
install: build
	 @poetry run pip install --upgrade dist/*.whl
.PHONY: install

# Upload to PyPi with poetry (with token if $$PYPI_TOKEN is specified)
upload:
	@[[ ! -z "$(PYPI_TOKEN)" ]] && poetry publish --username "__token__" --password $(PYPI_TOKEN) || poetry publish
.PHONY: upload

test:
	@# TODO Implement this properly!
	@# @poetry run python -m pytest --verbose tests/
	@for i in configs/config_*.yaml; do echo "Testing $${i}:"; $$(poetry env info -p)/bin/python \
		src/webarticlecurator/utils.py $${i} || exit 1; done
	for i in configs/extractors/site_specific_*.py; do $$(poetry env info -p)/bin/python $${i} || exit 1; done
	@echo "$(GREEN)All tests are successfully passed!$(NOCOLOR)"

clean: __clean-extra-deps
	@rm -rf dist/ .pytest_cache/ $$(poetry env info -p)
.PHONY: clean

# Do actual release with new version. Originally from: https://github.com/mittelholcz/contextfun
release-major:
	@make -s __release BUMP="major"
.PHONY: release-major

release-minor:
	@make -s __release BUMP="minor"
.PHONY: release-minor

release-patch:
	@make -s __release BUMP="patch"
.PHONY: release-patch

__release:
	@[[ "$(BUMP)" == "major" || "$(BUMP)" == "minor" || "$(BUMP)" == "patch" ]] || \
		(echo -e "$(RED)Do not call this target!\nUse 'release-major', 'release-minor' or 'release-patch'!$(NOCOLOR)"; \
		 exit 1)
	@[[ -z $$(git status --porcelain) ]] || (echo "$(RED)Working dir is dirty!$(NOCOLOR)"; exit 1)
	@# Update dependencies before buiding and testing (closest to clean install)
	@poetry update
	@# poetry version will modify pyproject.toml only. The other steps must be done manually.
	@poetry version $(BUMP)
	@# Add modified files to git before commit
	@git add pyproject.toml poetry.lock
	@# Clean install with (built package) and test
	@make all
	@# Create release commit and git tag
	@make -S __commit_to_origin NEWVER=$$(poetry run python src/$(MODULE)/version.py)
.PHONY: __release

__commit_to_origin:
	@[[ ! -z "$(NEWVER)" ]] || \
		(echo -e "$(RED)Do not call this target!\nUse 'release-major', 'release-minor' or 'release-patch'!$(NOCOLOR)"; \
		 exit 1)
	@echo "NEW VERSION: $(NEWVER)"
	@git commit -m "Release $(NEWVER)"
	@git tag -a "v$(NEWVER)" -m "Release v$(NEWVER)"
	@git push
	@git push --tags
.PHONY: __commit_to_origin
