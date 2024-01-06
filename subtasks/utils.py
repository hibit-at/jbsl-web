import os
import sys

import django


def setup_django():
    cwd = os.getcwd()
    sys.path.append(cwd)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jbsl3.settings")
    django.setup()
