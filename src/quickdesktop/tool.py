import pygtk
import sys
import gtk
import unittest
import os
import stat
pygtk.require("2.0")
import quickdesktop
from quickdesktop import plugin
from quickdesktop import common 
from quickdesktop import const
from quickdesktop import resource
from quickdesktop import templates

def setIcon(window):
    toolconf = ToolConf()
    icon = resource.getResource(toolconf.getIcon())
    if icon:
        window.set_icon_from_file(icon)

def quit_gtk(parent):
    message = "All unsaved changes willl be lost.\nAre you sure that you want to quit?"
    parent = parent or getToolWindow()
    d = gtk.MessageDialog(parent=parent, type=gtk.MESSAGE_QUESTION, message_format=message, buttons=gtk.BUTTONS_YES_NO)
    d.set_title("Warning")
    setIcon(d)
    response = d.run()
    d.destroy()
    if response==gtk.RESPONSE_YES:
        gtk.main_quit()

class ToolWindow(common.Singleton, gtk.Window):
    """
    Main tool window
    """
    def __init__(self):          
        if "toolconf" not in vars(self):
            gtk.Window.__init__(self,gtk.WINDOW_TOPLEVEL)
            self.resize(800,600)
            print "creating toolwindow"
            self.toolconf = ToolConf()
            self._setup()
            setIcon(self)

    def _setup(self):
        self.connect("delete_event", self.delete_event)
        
        from menus import MenuBar, Toolbar, createInstance
        self.menubar = createInstance(MenuBar,self.toolconf.getMenubar())
        self.toolbar = None
        self.set_title(self.toolconf.getTitle())
        self.vbox = gtk.VBox(False, 1)#homogeneous=False, spacing=1

        #child=mb,expand=False,fill=True,padding=0
        self.vbox.pack_start(self.menubar, False, True,0)
        if self.toolconf.getToolbar():
            self.toolbar = createInstance(Toolbar,self.toolconf.getToolbar())
            self.vbox.pack_start(self.toolbar, False, True, 0)
        
        self.lefthpaned = gtk.HPaned()
        self.righthpaned = None
        self.addSideBars(self.toolconf.getSidebars())

        self.desktoparea = gtk.VBox(True, 0)
        if self.righthpaned:
            self.righthpaned.add1(self.desktoparea)
        else:
            self.lefthpaned.add2(self.desktoparea)

        self.vbox.pack_start(self.lefthpaned,True,True,0)
        self.add(self.vbox)

    def addSideBars(self, sbars):
        self.sidebars = {}
        for sidebar in sbars:
            self.sidebars[sidebar] = self.createSidebar(sidebar)
            

    def createSidebar(self, sidebarid):
        data = plugin.PluginManager().getPlugin(sidebarid)['ITEMS'][0]
        code = """
from %(module)s import %(class)s
output['instance'] = %(class)s()"""
        
        output = {}
        g = {'output':output}
        eval(compile(code%data, "error.log", "exec"), g, g)

        if data['location'] == "left":
            self.lefthpaned.add1(output['instance'])
        else:
            if not self.righthpaned:
                self.righthpaned = gtk.HPaned()
                self.lefthpaned.add2(self.righthpaned)
            self.righthpaned.add2(output['instance'])

        return output['instance']

    def show(self):
        self.menubar.show()
        if self.toolbar: self.toolbar.show()
        self.lefthpaned.show()
        if self.righthpaned:
            self.righthpaned.show()
        for s in self.sidebars.keys():
            self.sidebars[s].show()
        self.desktoparea.show()
        self.vbox.show()
        gtk.Window.show(self)
        gtk.main()

    def delete_event(self, widget, event):
        print "delete_event", widget, event
        quit_gtk(widget)

class ToolConf(common.Singleton):

    def __init__(self):
        
        toolconf = plugin.PluginManager().getPlugin("toolconf")['ITEMS'][0]
        if "menubar" not in vars(self):
            self.menubar = self.loadMenubar(toolconf['menubar'])

        if 'toolbar' not in vars(self):
            if 'toolbar' not in toolconf:
                self.toolbar = None
            else:
                self.toolbar = self.loadToolbar(toolconf['toolbar'])

        self.title = toolconf['title']
        self.icon = toolconf['icon']
        self.sidebars = toolconf['sidebars']
        
    def loadToolbar(self, toolbarid):
        return plugin.PluginManager().getPlugin(toolbarid)

    def loadMenubar(self, menubarid):
        menubar = plugin.PluginManager().getPlugin(menubarid)
        menubar['ITEMS'] = [self.getMenu(item) for item in menubar['ITEMS']]
        return menubar

    def getMenu(self, menu):
        if type(menu)==type(""):
            return plugin.PluginManager().getPlugin(menu)
        return menu
        
    def getSidebars(self):
        return self.sidebars

    def getMenubar(self):
        return self.menubar

    def getToolbar(self):
        return self.toolbar

    def getTitle(self):
        return self.title

    def getIcon(self):
        return self.icon


class TestToolWindow(unittest.TestCase):

    def testToolWindowInstance(self):
        t1 = ToolWindow()
        print "Done creating first instance"
        t2 = ToolWindow()
        print "Done creating second instance"
        self.assertEqual(id(t1), id(t2))


def getToolWindow():
    tw = ToolWindow()
    print "ToolWindow : ", id(tw)
    return tw

def writeFile(path, data):
    f = open(path, "w")
    f.write(data)
    f.close()


def writePlugins(path):
    print "Creating plugins"
    data = {}
    data[os.path.join(path, "toolconf.plg")] = templates.toolconf
    data[os.path.join(path, "toolbar.plg")] = templates.toolbar
    data[os.path.join(path, "menubar.plg")] = templates.menubar
    data[os.path.join(path, "FileMenu.plg")] = templates.filemenu
    data[os.path.join(path, "HelpMenu.plg")] = templates.helpmenu
    data[os.path.join(path, "SampleMenu.plg")] = templates.samplemenu
    for k, v in data.items():
        writeFile(k, v)

def writeConfig(path):
    print "Creating configurations"
    data = {}
    data[os.path.join(path, "sample.conf")] = templates.sampleconf
    data[os.path.join(path, "sample1.conf")] = templates.sample1conf
    for k,v in data.items():
        writeFile(k, v)

def writeResources(path):
    print "Creating resources"
    writeFile(os.path.join(path, "config.tree"), templates.conftree)
    f = open(os.path.join(path, "qdesktop-logo.ppm"), "w")
    for line in templates.logo:
        f.write(str(line) + "\n")
    f.close()

def createTool(name):
    cwd = os.getcwd()
    toolfolder = os.path.join(cwd, name)
    print "Creating folder structure"
    os.mkdir(toolfolder)
    plugins = os.path.join(toolfolder, "plugins")
    config = os.path.join(toolfolder, "config")
    resources = os.path.join(toolfolder, "resources")
    map(os.mkdir, [plugins, config, resources])
    writePlugins(plugins)
    writeConfig(config)
    writeResources(resources)
    executable = os.path.join(toolfolder, name)
    writeFile(executable, templates.mainscript%toolfolder)
    perms = stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IROTH
    os.chmod(executable, perms)


if __name__ == "__main__":
    print sys.argv
    const.home = "/home/vikrant/programming/work/rep/sample"
    unittest.main()


    
    
