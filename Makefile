.PHONY: test dist

test:
	python setup.py test

dist:
	rm -rf dist
	python setup.py bdist_wheel && twine upload dist/*
