all:
	@echo "See Makefile for possible targets!"

build:
	python3 setup.py sdist bdist_wheel

upload:
	python3 -m twine upload dist/*

clean:
	rm -rf dist/ build/ webarticlecurator.egg-info/
