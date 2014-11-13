# -*- coding: utf-8 -*-
from eloue.settings import *

SITE_ID = 13

SESSION_COOKIE_DOMAIN = 'go-sport.fr' # FIXME!

CACHE_MIDDLEWARE_KEY_PREFIX = 'gosport'

for key in PIPELINE_CSS:
    output_filename = PIPELINE_CSS[key]['output_filename'].replace('.css', '_gosport.css')
    PIPELINE_CSS[key]['output_filename'] = output_filename

TEMPLATE_DIRS = env('TEMPLATE_DIRS', (
    local_path('templates/gosport'),
    local_path('templates/'),
))