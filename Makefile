PY ?= .venv/bin/python
PELICAN ?= .venv/bin/pelican
PELICANOPTS =

INPUTDIR = content
OUTPUTDIR = output
CONFFILE = pelicanconf.py
PUBLISHCONF = publishconf.py

SLURM_SNAPSHOT_OUT = content/data/cluster_status.json

help:
	@echo "make install       - create venv + install Python/Node deps"
	@echo "make css           - build Tailwind/DaisyUI CSS once"
	@echo "make css-watch     - rebuild CSS on change (run alongside devserver)"
	@echo "make html          - build the static site into output/ (dev config)"
	@echo "make publish       - build the static site with publishconf.py"
	@echo "make devserver     - serve output/ at http://localhost:8000 with autoreload"
	@echo "make slurm-snapshot- poll Slurm and refresh content/data/cluster_status.json"
	@echo "make clean         - remove build output"

install:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt
	npm install

css:
	npm run css:build

css-watch:
	npm run css:watch

html: css
	$(PELICAN) $(INPUTDIR) -o $(OUTPUTDIR) -s $(CONFFILE) $(PELICANOPTS)

publish: css
	$(PELICAN) $(INPUTDIR) -o $(OUTPUTDIR) -s $(PUBLISHCONF) $(PELICANOPTS)

devserver: css
	$(PELICAN) $(INPUTDIR) -o $(OUTPUTDIR) -s $(CONFFILE) -r --listen $(PELICANOPTS)

slurm-snapshot:
	$(PY) scripts/slurm_snapshot.py -o $(SLURM_SNAPSHOT_OUT)

clean:
	rm -rf $(OUTPUTDIR)

.PHONY: help install css css-watch html publish devserver slurm-snapshot clean
