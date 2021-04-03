.PHONY: test dist

test:
	pip install -e .[test] && pytest -v --cov

format:
	pysen run format

dist:
	rm -rf dist
	python setup.py bdist_wheel && twine upload dist/*
