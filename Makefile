.DEFAULT_GOAL = all
RED := $(shell tput setaf 1)
GREEN := $(shell tput setaf 2)
NOCOLOR := $(shell tput sgr0)
PYTHON := python3
VENVDIR := $(CURDIR)/venv
VENVPIP := $(VENVDIR)/bin/python -m pip
VENVPYTHON := $(VENVDIR)/bin/python

all:
	@echo "See Makefile for possible targets!"

venv:
	@echo "Creating virtualenv in $(VENVDIR)...$(NOCOLOR)"
	@rm -rf $(VENVDIR)
	@$(PYTHON) -m venv $(VENVDIR)
	@$(VENVPIP) install wheel twine
	@$(VENVPIP) install -r requirements.txt
	@echo "$(GREEN)Virtualenv is succesfully created!$(NOCOLOR)"
.PHONY: venv

build:
	$(VENVPYTHON) setup.py sdist bdist_wheel

install: build
	@echo "Installing package to user..."
	$(VENVPIP) install --upgrade dist/*.whl
	@echo "$(GREEN)Package is succesfully installed!$(NOCOLOR)"
.PHONY: install

upload:
	$(VENVPYTHON) -m twine upload dist/*

clean:
	rm -rf dist/ build/ webarticlecurator.egg-info/

test:
	for i in configs/config_*.yaml; do echo "Testing $${i}:"; $(VENVPYTHON) webarticlecurator/utils.py $${i} \
	 || exit 1; done
	for i in configs/extractors/site_specific_*.py; do $(VENVPYTHON) $${i} || exit 1; done
	@echo "$(GREEN)All tests are succesfully passed!$(NOCOLOR)"
