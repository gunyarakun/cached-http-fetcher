.PHONY: test dist

test:
	pip install -e .[test] && pytest -v --cov


dist:
	rm -rf dist
	python setup.py bdist_wheel && twine upload dist/*
