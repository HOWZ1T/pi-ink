.PHONY: lint
lint:
	black ./pi_ink
	isort ./pi_ink
