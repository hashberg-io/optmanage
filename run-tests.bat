@echo off
mypy --strict optmanage
pylint optmanage
pytest test --cov=./optmanage
coverage html
@pause
