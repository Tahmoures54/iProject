run:
	flask run --debug

test:
	pytest

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
