

class _const(object):
    """
    Class for creating constants which can not be changed.
    taken from python reciepies.
    """
    class ConstError(TypeError): pass

    def __setattr__(self, name, value):
        if name in self.__dict__:
            raise self.ConstError, "Can't rebind const(%s)" % name
        self.__dict__[name] = value
        
        
    def __delattr__(self, name):
        if name in self.__dict__:
            raise self.ConstError, "Can't unbind const(%s)" % name
        raise NameError, name


c = _const()
# default tool directories 
# directory paths with respect to 'home', which will be set in tool 
# creation.

# resources - for icons/images and other media files
c.resources = "resources"

# directory where all configurations are stored
c.config = "config"
c.configsavespace = "config-save"

# directory where all plugins are stored. All plugins will be 
# loaded from this directory.
c.plugins = "plugins"

# directory where extra binaries will be saved
c.bin = "bin"

import sys
sys.modules[__name__] = c
