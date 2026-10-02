import sys
import os

sys.path.append(os.curdir)
from pelicanconf import *  # noqa

# Set this to the real, published URL when you deploy (e.g. https://hpc.coe.example.ac.th)
SITEURL = "https://hpc.example.ac.th"
RELATIVE_URLS = False

FEED_ALL_ATOM = "feeds/all.atom.xml"
CATEGORY_FEED_ATOM = "feeds/{slug}.atom.xml"

DELETE_OUTPUT_DIRECTORY = True

# Performance / SEO
GZIP_CACHE = True
