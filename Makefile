format:
	black . -l 79

test:
	pytest tests --disable-warnings
