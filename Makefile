build: clean
	python3 setup.py sdist bdist_wheel

clean:
	rm -rf build dist

requirements:
	pip3 install -r requirements.txt 
	pip3 install -r requirements-test.txt
.PHONY: requirements

fmt:
	black .

check-fmt:
	black --check .
.PHONY: check-fmt

check-lint:
	pylint snowlock
.PHONY: check-lint

check-type:
	mypy snowlock
.PHONY: check-type

check: check-fmt check-lint check-type
.PHONY: check

test:
	python3 -m unittest tests
.PHONY: test

dev-install: build
	pip3 uninstall -y snowlock && pip3 install dist/snowlock-*-py3-none-any.whl
.PHONY: dev-install
