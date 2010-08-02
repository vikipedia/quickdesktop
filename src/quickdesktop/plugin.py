from quickdesktop.common import Singleton, DataManager, DataParser
from quickdesktop import const
import os

class PluginManager(DataManager):
    """
    PluginManager manages plugins in system
    """
    def __init__(self):
        DataManager.__init__(self, "plugins", ".plg")

    def _loadData(self, plg):
        print "*** Loading %s %s " % (self.datatype, plg)
        filename = os.sep.join([self._getDataDir(),plg])
        pdata = DataParser(filename).getData()
        self.data[pdata['id']]  = pdata

    def getPlugin(self, id):
        return self.getData(id)

print __name__
if __name__=="__main__":
    const.home = "/home/vikrant/programming/work/rep/sample"
    pm = PluginManager()
    pm1 = PluginManager()
    pm2 = PluginManager()
    print id(pm), id(pm1), id(pm2)
    print pm.data.keys()
