import pygtk, sys, gtk, unittest
pygtk.require("2.0")
import quickdesktop
from quickdesktop.plugin import PluginManager 
from quickdesktop import common 
from quickdesktop import const
from quickdesktop import resource


def setIcon(window):
    icon = resource.getResource("resource:logo.xpm")
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

        self.vbox = gtk.VBox(False, 1)#homogeneous=False, spacing=1

        #child=mb,expand=False,fill=True,padding=0
        self.vbox.pack_start(self.menubar, False, True,0)
        if self.toolconf.getToolbar():
            self.toolbar = createInstance(Toolbar,self.toolconf.getToolbar())
            self.vbox.pack_start(self.toolbar, False, True, 0)

        self.hp = gtk.HPaned()
        self.vbox.pack_start(self.hp,True,True,0)
        self.add(self.vbox)
    
    def show(self):
        self.menubar.show()
        if self.toolbar: self.toolbar.show()
        self.hp.show()
        self.vbox.show()
        gtk.Window.show(self)
        gtk.main()

    def delete_event(self, widget, event):
        print "delete_event", widget, event
        quit_gtk(widget)

class ToolConf(common.Singleton):

    def __init__(self):
        
        toolconf = PluginManager().getPlugin("toolconf")['ITEMS'][0]
        if "menubar" not in vars(self):
            self.menubar = self.loadMenubar(toolconf['menubar'])

        if 'toolbar' not in vars(self):
            if 'toolbar' not in toolconf:
                self.toolbar = None
            else:
                self.toolbar = self.loadToolbar(toolconf['toolbar'])

        self.sidebars = toolconf['sidebars']
        
    def loadToolbar(self, toolbarid):
        return PluginManager().getPlugin(toolbarid)

    def loadMenubar(self, menubarid):
        menubar = PluginManager().getPlugin(menubarid)
        menubar['ITEMS'] = [self.getMenu(item) for item in menubar['ITEMS']]
        return menubar

    def getMenu(self, menu):
        if type(menu)==type(""):
            return PluginManager().getPlugin(menu)
        return menu
        
    def getSidebars(self):
        return self.sidebars

    def getMenubar(self):
        return self.menubar

    def getToolbar(self):
        return self.toolbar


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


print __name__
if __name__ == "__main__":
    print sys.argv
    const.home = "/home/vikrant/programming/work/rep/quickdesktop"
    unittest.main()


    
    
