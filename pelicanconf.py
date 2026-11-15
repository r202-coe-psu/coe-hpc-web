AUTHOR = "CoE HPC Team"
SITENAME = "CoE HPC"
SITESUBTITLE = "CoE Mini High-Performance Computing"
SITEURL = ""

PATH = "content"
TIMEZONE = "Asia/Bangkok"
DEFAULT_LANG = "en"

THEME = "theme"

# Content layout -------------------------------------------------------
PAGE_PATHS = ["pages"]
ARTICLE_PATHS = ["articles"]
STATIC_PATHS = ["images", "data"]

ARTICLE_URL = "news/{slug}/"
ARTICLE_SAVE_AS = "news/{slug}/index.html"
PAGE_URL = "{slug}/"
PAGE_SAVE_AS = "{slug}/index.html"

ARCHIVES_SAVE_AS = "news/index.html"
DIRECT_TEMPLATES = ["index", "archives"]

DEFAULT_PAGINATION = 8

# Feeds are not needed while developing locally
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

DEFAULT_METADATA = {
    "status": "published",
}

# Primary navigation shown in the theme's navbar
MENUITEMS = (
    ("Home", "/"),
    ("Getting Started", "/getting-started/"),
    ("Documentation", "/documentation/"),
    ("News", "/news/"),
    ("Contact", "/contact/"),
)

# Slurm cluster status plugin ------------------------------------------
PLUGIN_PATHS = ["plugins"]
PLUGINS = ["slurm_status"]

# Where the snapshot script (scripts/slurm_snapshot.py) writes live data.
# Falls back to SLURM_STATUS_SAMPLE_JSON when this file does not exist yet,
# so `pelican content` works out of the box on a laptop with no Slurm access.
SLURM_STATUS_JSON = "content/data/cluster_status.json"
SLURM_STATUS_SAMPLE_JSON = "content/data/cluster_status.sample.json"

DEFAULT_PAGINATION = 8

RELATIVE_URLS = False
