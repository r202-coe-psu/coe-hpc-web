import sys
import os

sys.path.append(os.curdir)
from pelicanconf import *  # noqa

# Public URL of the deployed site (e.g. https://hpc.coe.psu.ac.th), taken from
# the SITEURL env var / Docker build arg. Empty -> root-relative links ("/theme/..."),
# which work on any host or port.
SITEURL = os.environ.get("SITEURL", "").rstrip("/")
RELATIVE_URLS = False

FEED_ALL_ATOM = "feeds/all.atom.xml"
CATEGORY_FEED_ATOM = "feeds/{slug}.atom.xml"

DELETE_OUTPUT_DIRECTORY = True

# Performance / SEO
GZIP_CACHE = True
