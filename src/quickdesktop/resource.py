from quickdesktop.common import Singleton
from quickdesktop import const
import os, re

resourcepattern = re.compile("resource:(.+)")

def getResource(name):
    match = re.match(resourcepattern, name)

    if match:
        path = os.sep.join([const.home, const.resources, match.groups()[0]])
        if os.path.exists(path): return path
