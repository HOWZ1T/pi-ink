.PHONY: lint
lint:
	black ./pi-ink
	isort ./pi-ink
