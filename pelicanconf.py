#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = u'Matthew Stickney'
SITENAME = u'FiddlyBits'
SITEURL = ''

ARTICLE_URL = 'posts/{date:%Y}/{date:%m}/{date:%d}/{slug}.html'
ARTICLE_SAVE_AS = ARTICLE_URL

PATH = 'content'

TIMEZONE = 'America/New_York'

DEFAULT_LANG = u'en'

# Use typographical enhancements
TYPOGRIFY='true'

THEME='pelican-octopress-theme'
# pelican-octopress configuration
GITHUB_USER='mtstickney'
GITHUB_REPO_COUNT='50'
GITHUB_SHOW_USER_LINK='true'
GITHUB_SKIP_FORK='true'
SITESUBTITLE='A technical blog about fiddly things.'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Blogroll
LINKS = ()

# Social widget
SOCIAL = ()

DEFAULT_PAGINATION = 10

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True
