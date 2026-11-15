PY ?= poetry run python
PELICAN ?= poetry run pelican
PELICANOPTS =

INPUTDIR = content
OUTPUTDIR = output
CONFFILE = pelicanconf.py
PUBLISHCONF = publishconf.py

SLURM_SNAPSHOT_OUT = content/data/cluster_status.json
# Slurm login node queried over SSH for the homepage status widget.
# Override with `make slurm-snapshot SLURM_HOST=` to run sinfo/squeue locally.
SLURM_HOST ?= nillapat.coe.psu.ac.th
SLURM_CLUSTER_NAME ?= Nillapat

help:
	@echo "make install       - install Python deps (Poetry) + Node deps"
	@echo "make css           - build Tailwind/DaisyUI CSS once"
	@echo "make css-watch     - rebuild CSS on change (run alongside devserver)"
	@echo "make html          - build the static site into output/ (dev config)"
	@echo "make publish       - build the static site with publishconf.py"
	@echo "make devserver     - serve output/ at http://localhost:8000 with autoreload"
	@echo "make slurm-snapshot- poll Slurm on $$SLURM_HOST (nillapat) over SSH, refresh content/data/cluster_status.json"
	@echo "make docker-build  - build the production Docker image"
	@echo "make docker-run    - run the production Docker image on :8000"
	@echo "make deploy        - build + (re)start the site with docker compose"
	@echo "make deploy-down   - stop the docker compose deployment"
	@echo "make clean         - remove build output"

install:
	poetry install --no-root
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
	$(PY) scripts/slurm_snapshot.py -o $(SLURM_SNAPSHOT_OUT) --host "$(SLURM_HOST)" --cluster-name "$(SLURM_CLUSTER_NAME)"

docker-build:
	docker build -t coe-hpc-web .

docker-run:
	docker run --rm -p 8000:80 coe-hpc-web

# Refresh the Slurm snapshot first so the image bakes in current status.
# A failed snapshot (e.g. cluster unreachable) keeps the previous one.
deploy:
	-$(MAKE) slurm-snapshot
	docker compose up -d --build

deploy-down:
	docker compose down

clean:
	rm -rf $(OUTPUTDIR)

.PHONY: help install css css-watch html publish devserver slurm-snapshot docker-build docker-run deploy deploy-down clean
