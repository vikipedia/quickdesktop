from quickdesktop import const
from quickdesktop import common

import os
import gtk
import pygtk
import unittest
pygtk.require("2.0")


class ConfigurationManager:

    def __init__(self, savespace=None):
        if savespace:
            self.savespace = savespace
        else:
            self.savespace = const.configsavespace

    def getFileName(self, confid):
        return confid + ".conf"

    def _getConfFilePath(self, confid):
        return os.path.join(const.home, self.getConfigDir(), self.getFileName(confid))

    def getConfigDir(self):
        return  vars(const)['config']

    def _getSavedFilePath(self, confid):
        try:
            os.mkdir(self.savespace)
            os.mkdir(os.path.join(self.savespace, self.getConfigDir()))
        except:
            pass

        return os.path.join(self.savespace, self.getConfigDir(), self.getFileName(confid))

    def getConfiguration(self, confid):
        path = self._getConfFilePath(confid)
        path2 = self._getSavedFilePath(confid)
        if os.path.exists(path2):
            path = path2

        return common.DataParser(path).getData()

    def getConfigValue(self, id):
        """
        assumes configuration id in the format
        confid:quickid
        """
        confid, quickid = id.split(":")
        conf = self.getConfiguration(confid)
        return [i['value'] for i in conf['ITEMS'] if i['quickid']==quickid][0]

    def discard(self, confid):
        if os.path.exists(self._getConfFilePath(confid)) and os.path.exists(self._getSavedFilePath(confid)):
            os.unlink(self._getSavedFilePath(confid))

    def save(self, confid, values):
        if not os.path.exists(self._getConfFilePath(confid)):
            d = common.DataParser(self._getSavedFilePath(confid)).getData()
        else:
            d = common.DataParser(self._getConfFilePath(confid)).getData()
        flag = False

        for item in d['ITEMS']:
            quickid = item['quickid']
            default = item['value']
            if quickid in values:
                conf = values[quickid]
                if default!=conf:
                    flag = True
                    item['value'] = conf
        if flag:
            print "** Saving configuration ",confid
            self._writeConfiguration(d, self._getSavedFilePath(confid))
        else:
            # this means data is same .. so no need to save!
            # delete stale data
            self.discard(confid)

    def _writeConfiguration(self, confdata, filename):
        dirname = os.path.dirname(filename)
        try:
            os.mkdir(dirname)
        except:
            pass

        f = open(filename, "w")

        def writeFields(x,y,f):
            f.write("\n%s\t\t%s"%(x,y))

        writeFields("version","1.0",f)
        writeFields("type","configuration",f)
        writeFields("id", confdata['id'],f)

        f.write("\n")

        if "CODE" in confdata:
            f.write("\n%% CODE")
            f.write("\n{{{")
            f.write("\n" + confdata['CODE'])
            f.write("\n}}}")
            f.write("\n")
            
        f.write("\n%% ITEMS")

        for item in confdata['ITEMS']:
            for k,v in item.items():
                writeFields(k,v,f)
            f.write("\n")

        f.close()


def getConfiguration(confid, savelocation=None):
    return ConfigurationManager(savespace = savelocation).getConfiguration(confid)

def getConfigValue(confid, savelocation=None):
    """
    assumes configuration id in the format
    confid:quickid
    """
    return ConfigurationManager(savespace=savelocation).getConfigValue(confid)

class TestConf(unittest.TestCase):
    
    def setUp(self):
        try:
            const.home = "/home/vikrant/programming/work/rep/sample"
        except:
            pass

    def check(self, d):
        self.assertEqual(d['id'], 'sample')
        self.assertEqual(len(d['ITEMS']), 5)

    def testConf(self):
        d = getConfiguration("sample", "unittest")
        self.check(d)
    
    def check2(self, loc, name):
        location = os.path.join(const.home, loc)
        try:
            os.mkdir(location)
        except:
            pass

        c = ConfigurationManager(savespace=location)
        d = c.getConfiguration(name)
        c.save(name, {'b':50})
        d1 = c.getConfiguration(name)
        self.assertEqual(d1['id'], d['id'])
        self.assertEqual(len(d1['ITEMS']),len(d['ITEMS']))
        self.assertEqual(d1['ITEMS'][1]['value'], 50)
        c.save(name, {})
        d1 = c.getConfiguration(name)
        self.assertEqual(d1['ITEMS'][1]['value'], 100)
        c.discard(name)
        c.save(name, {})

    def testWrite(self):
        self.check2("test1", "sample")
        self.check2("test2", "sample")
     
if __name__=="__main__":
    unittest.main()



