import os
import re
from quickdesktop import const
import unittest

class Singleton(object):
    """ A Pythonic singleton """

    def __new__(cls, *args, **kwargs):
        """
        this method is static method (i.e. called before instance creation).
        This is called to create new instance of the object.
        """
        if '_instsingle' not in vars(cls):
            cls._instsingle = super(Singleton,cls).__new__(cls)
        return cls._instsingle

class ListValue(list):

   def __init__(self, iterable):
	list.__init__(self, iterable)
            
   def __repr__(self):
        return ",".join([str(i) for i in self])
        
class TestSingleton(unittest.TestCase):
    
    def testSingleton(self):
        class A(Singleton):
            pass

        a1 = A()
        a2 = A()
        self.assertEqual(id(a1), id(a2))
                
    def testSingleton2(self):
        class A(Singleton):
            
            def __init__(self, value):
                if "flag" not in vars(self):
                    self.flag = value        

        a1 = A(True)
        a2 = A(False)
        self.assertEqual(a1, a2)
        self.assertEqual(a1.flag, a2.flag)

    def testSingleton3(self):
        class A(Singleton):
            
            def __init__(self):
                if "flag" not in vars(self):
                    self.flag = True
                else:
                    self.flag = not self.flag
        
        a1 = Singleton()

        s = """
a2 = Singleton()
"""
        eval(compile(s, "error.log", "exec"), globals(), locals())
        self.assertEqual(id(a1), id(locals()['a2']))
        #eval(compile("a2=A()", "error.log", "exec"), globals(), locals())
        #self.assertEqual(a1.flag, locals()['a2'].flag)

class DataManager(Singleton):
    """
    DataManager manages data in system
    """
    def __init__(self, datatype, extn):
        """
        Starts with empty data cache
        """
        self.datatype = datatype
        self.extn = extn
        if "data" not in vars(self):
            self.data = {}
            self.loadAll()

    def loadAll(self):
        """
        Load all data from system into cache
        """
        plgs = self._getAllDataFiles(self._getDataDir())
        for plg in plgs:
            self._loadData(plg)

    def _loadData(self, plg):
        print "*** Loading %s %s " % (self.datatype, plg)
        filename = os.sep.join([self._getDataDir(),plg])
        pdata = DataParser(filename).getData()
        self.data[pdata['id']]  = pdata

    def _getDataDir(self):
        location = self.datatype
        try:
            location = vars(const)[self.datatype]
        except:
            pass
        return os.sep.join([const.home, location]) 

    def _getAllDataFiles(self, datadir):
        """
        Returns all data files from system.
        """
        return [file for file in os.listdir(datadir) if file.endswith(self.extn)]

    def getData(self, id):
        return self.data[id]


class DataParser:
    fields = re.compile("(\S+)\s+(.+)\s*")
    singleword = re.compile("(\S+)\s*")
    empty = re.compile("\s*\n")
    section = re.compile("^%% ([A-Z0-9]+)")
    codeEnv = {}

    def __init__(self, datafile):
        self.data = self.parsedata(datafile)

    def getData(self):
        return self.data

    def getWord(self, s):
        return re.match(self.singleword, s).groups()[0]

    def getPair(self,s):
        return re.match(self.fields, s).groups()


    def getCodeSection(self, currentline, f):
        code = []
        currentline = f.readline()
        while not currentline.startswith("}}}"):
            code.append(currentline)
            currentline = f.readline()
        return "".join(code), currentline


    def parseDictionaryItem(self, f, currentline):
        match1 = re.match(self.fields, currentline)
        match2 = re.match(self.singleword, currentline)
        if match1:
            x,y = match1.groups()
            try:
                return x, eval(y,self.codeEnv,self.codeEnv)
            except:
                return x,y.strip()
        elif match2:
            currentline = f.readline()

            if currentline.startswith("{{{"):
                code, currentline  = self.getCodeSection(currentline, f)

            return match2.groups()[0],code
        else:
            raise Exception("Invalid format")
            
    def addData(self, sectiondata, subsection):
        if type(subsection)==type(""):
            sectiondata = subsection
            subsection = []
        elif type(subsection)==type([]):
            map(sectiondata.append, subsection)
            subsection = []
        else:
            sectiondata.append(subsection)
            subsection = {}
        return sectiondata, subsection

    def parseSubSectionItem(self,f, line, datatype, subsection):
        if not datatype:
            if line.startswith("{{{"):
                subsection, line  = self.getCodeSection(line, f)
                eval(compile(subsection, "error.log", "exec"), self.codeEnv, self.codeEnv)
            elif re.match(self.fields, line):
                k, v = self.getPair(line)
                subsection = {k:v.strip()}
            else:
                subsection = [self.getWord(line)]
            datatype = type(subsection)
        elif datatype==type({}):
            k, v = self.parseDictionaryItem(f, line)
            subsection[k] = v
        elif datatype==type(""):
            pass # code has been parsed! now skip all lines till next section
        else:
            subsection.append(self.getWord(line))
        return datatype, subsection

    def parsedata(self, datafile):
        f = open(datafile)
        d = {}
        line = f.readline()

        # skip empty lines and comments
        while re.match(self.empty, line) or line.startswith("#"): line = f.readline()    
        while not re.match(self.section, line):
            try:
                k, v = self.parseDictionaryItem(f, line)
                d[k] = v
            except Exception, e:
                pass
            line = f.readline()

        sectiondata  = []
        subsection = {}
        sectionstart = False
        sectionheader = None
        while line:
            if re.match(self.section, line):
                if subsection:
                    sectiondata, subsection = self.addData(sectiondata, subsection)
                d[sectionheader] = sectiondata
                sectiondata = []

                match = re.match(self.section, line)
                sectionheader = match.groups()[0]
                datatype = None
                line = f.readline()
                continue
            elif re.match(self.empty, line):
                if subsection:
                    sectiondata, subsection = self.addData(sectiondata, subsection)
                datatype = None
                line = f.readline()
                continue

            datatype, subsection = self.parseSubSectionItem(f, line, datatype, subsection)
            line = f.readline()

        f.close()
        if subsection:
            sectiondata, subsection = self.addData(sectiondata, subsection)
        d[sectionheader] = sectiondata
        return d

class TestParser:
    
    def getDataItems(self):
        menu = """    
version		1.0
type		menu
id		FileMenu
name		_File
sensitiveon	None
insensitiveon	None
sensitive	True

%% CODE
{{{
def negate(a):
    return not a
}}}

%% ITEMS
name		_Open 
tooltip		Open
insensitiveon	SOME_EVENT1
sensitiveon	SOME_EVENT2
sensitive	negate(True)
action
{{{
multicaster.dispatchEvent("SOME_EVENT1",{'origin':"_Open"})
}}}
   
name		_Save
tooltip		Save
insensitiveon	SOME_EVENT2
sensitiveon	SOME_EVENT1
sensitive	False
action
{{{
multicaster.dispatchEvent("SOME_EVENT2",{'origin':"_Open"})
}}}
"""
        menubar = """
version		1.0
type		menu.MenuBar
id		mainmenubar
sensitiveon	None
insensitiveon	None
sensitive	True

%% ITEMS
FileMenu
HelpMenu
"""
        toolbar = """
version		1.0
type		menu.Toolbar
id		toolbar
sensitiveon	None
insensitiveon	None
sensitive	True

%% ITEMS
name		Open
tooltip		Open
icon		resource:brasero.png
insensitiveon	SOME_EVENT1
sensitiveon	SOME_EVENT2
sensitive	True
action
{{{
from quickdesktop.events import EventMulticaster
EventMulticaster().dispatchEvent("SOME_EVENT1",{'origin':self})
print "Open"
}}}

name		Save
tooltip		Save
icon		resource:brasero.png
insensitiveon	SOME_EVENT2
sensitiveon	SOME_EVENT1
sensitive	False
action
{{{
print "Save"
}}}
"""
        return {'menu':menu, 'menubar':menubar, 'toolbar':toolbar}

    def setUp(self):
        items = self.getDataItems()
        self.filenames = items.keys()
        [self.writeFile(item , name) for name, item in items.items()]

    def tearDown(self):
        [os.unlink(f) for f in self.filenames]

    def writeFile(self, item, name):
        f = open(name, "w")
        f.write(item)
        f.close()
    
class TestDataParse(TestParser, unittest.TestCase):

    def testMenubar(self):
        p = DataParser('menubar')
        d = p.getData()
        self.assertEqual(d['version'], 1.0)
        self.assertEqual(d['type'], 'menu.MenuBar')
        self.assertEqual(len(d['ITEMS']), 2)
        self.assertEqual(d['ITEMS'][0],'FileMenu')
        self.assertEqual(d['ITEMS'][1],"HelpMenu")
        #self.assertEqual(d['ITEMS'][0]['sensitive'], False)

    def testMenu(self):
        p = DataParser('menu')
        d = p.getData()
        self.assertEqual(d['version'], 1.0)
        self.assertEqual(d['id'], 'FileMenu')
        self.assertEqual(len(d['ITEMS']), 2)
        self.assertEqual(d['ITEMS'][0]['name'],'_Open')
        action = """multicaster.dispatchEvent("SOME_EVENT2",{'origin':"_Open"})
"""
        self.assertEqual(d['ITEMS'][1]['action'],action)
        code = """def negate(a):
    return not a
"""
        self.assertEqual(d['CODE'], code)

    def testToolbar(self):
        p = DataParser('toolbar')
        d = p.getData()
        self.assertEqual(d['ITEMS'][0]['icon'], "resource:brasero.png")

def writeTree(tree, filename):
    def write(tree, f, indent):
        f.write("\n")
        if type(tree)==type([]):
            f.write(indent + "* " + tree[0])
            indent = indent + "\t"
            [write(node, f, indent) for node in tree[1:]]
        else:
            f.write(indent + "+ " + tree)


    f = open(filename, "w")
    [write(node, f, "") for node in tree[1:]] # skip root!
    f.close()
        
    
def parseTree(treefile, loadItem = lambda x: x, root="root"):
    f = open(treefile)
    tree = [root]
    offset = None
    stack = [(tree, offset)]

    folder = re.compile("([ \t]*)\*[ \t]*([\w ]+)")
    item = re.compile("([ \t]*)\+[ \t]*(\w+)")
    
    for line in f.xreadlines():
        m1 = re.match(folder, line)
        m2 = re.match(item, line)
        
        if m1:
            offset = m1.groups()[0]
            foldername = m1.groups()[1]
            l = [foldername]

            while stack[-1][0][0]!=root and len(offset) <= len(stack[-1][1]):
                stack.pop()

            stack[-1][0].append(l)
            stack.append((l, offset))

        elif  m2:
            offset = m2.groups()[0]
            itemname = m2.groups()[1]
            while stack[-1][1] and len(offset) <= len(stack[-1][1]):
                stack.pop()

            stack[-1][0].append(loadItem(itemname))
        else:
            continue

    return tree

class TestParseTree(TestParser, unittest.TestCase):

    def getDataItems(self):
        treetext = """
* A
  + item
* Test Folder
  * Subfolder
    + item1
  * Subfolder2
    * f
      * f2
      	+ i
    + item3
    * x
* Sample
  + sample
  * subfolder
    + item2"""
        return {'treetext':treetext}

    def testParseTree(self):
        t = parseTree('treetext',root="root")
        self.assertEqual(t[0],"root") # check root
        map(lambda x,y: self.assertEqual(x[0],y), t[1:],['A','Test Folder','Sample'])
        self.assertEqual(t[1][1], 'item')
        self.assertEqual(t[2][1][0], 'Subfolder')
        self.assertEqual(t[2][1][1], 'item1')
        self.assertEqual(t[2][2][0],'Subfolder2')
        self.assertEqual(t[2][2][1][0], 'f')
        self.assertEqual(t[2][2][1][1][0], 'f2')
        self.assertEqual(t[2][2][1][1][1], 'i')
        self.assertEqual(t[2][2][2], 'item3')
        self.assertEqual(t[2][2][3][0], 'x')
        self.assertEqual(t[3][1], 'sample')
        self.assertEqual(t[3][2][0], 'subfolder')
        self.assertEqual(t[3][2][1], 'item2')

    def testWriteTree(self):
        t = parseTree('treetext', root='root')
        writeTree(t, 'treetext')
        self.testParseTree()

if __name__=="__main__":
    unittest.main()
