from quickdesktop import common
from quickdesktop import const
import os

class PluginManager(common.DataManager):
    """
    PluginManager manages plugins in system
    """
    def __init__(self):
        common.DataManager.__init__(self, "plugins", ".plg")

    def getPlugin(self, id):
        return self.getData(id)

if __name__=="__main__":
    const.home = "/home/vikrant/programming/work/rep/sample"
    pm = PluginManager()
    pm1 = PluginManager()
    pm2 = PluginManager()
    print id(pm), id(pm1), id(pm2)
    print pm.data.keys()
