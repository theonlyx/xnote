.PHONY: build clean
build:xnote.pyz
xnote.pyz:xnote/app.py xnote/cli.py xnote/db.py xnote/__main__.py Pipfile.lock
	pipenv run pip freeze  > requirements.txt
	python3 -m pip install -r requirements.txt --upgrade --target xnote
	python3 -m zipapp xnote -p "/usr/bin/env python3" --compress
clean:
	rm -f xnote.pyz
	rm -f requirements.txt
	rm -rf xnote/__pycache__
	rm -rf xnote/*~
	rm -rf xnote/sqlalchemy
	rm -rf xnote/SQLAlchemy*
	rm -rf xnote/yaml
	rm -rf xnote/PyYAML*
	rm -rf xnote/six*
	rm -rf xnote/sqlalchemy_utils
	find xnote/ -name \*.pyc -type f -print0|xargs -0 -I{} rm {}
