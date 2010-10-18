import pygtk
import sys
import gtk
import unittest
from quickdesktop import resource
from quickdesktop import events
from quickdesktop import common
pygtk.require("2.0")

def createEventFunction(eventType,sensitive):
    CODE = """
def %s(self, eventdata):
	self.set_sensitive(sensitive)"""

    funcname = events.getFunctionName(eventType)
    g = {'funcname':funcname, 'sensitive':sensitive}
    eval(compile(CODE%funcname,"error.log","exec"),g,g)
    return g[funcname]

def getEvents(plugindata):
    sensitiveEvents = []
    insensitiveon = []
    if plugindata['sensitiveon']!=None:
        sensitiveEvents = [e for e in plugindata['sensitiveon'].split(",")]
    if plugindata['insensitiveon']!=None:
        insensitiveon = [e for e in plugindata['insensitiveon'].split(",")]
    return sensitiveEvents,insensitiveon

def createInstance(claz, plugindata, data={}):
    instance = claz(plugindata, data=data)
    addEventsHandling(instance, plugindata)
    return instance

def addEventsHandling(instance, plugindata):
    def addListener(_events, value, instance):
        for e in _events:
            func = createEventFunction(e, value)
            events.EventMulticaster().addListener(e, instance, func)
    sensitiveEvents, insensitiveon = getEvents(plugindata)

    addListener(sensitiveEvents, True, instance)
    addListener(insensitiveon, False, instance)


class Toolbar(gtk.Toolbar):
    
    def _getIconPath(self, resourceid):
        return resource.getResource(resourceid)

    def __init__(self, toolbardata, data={}):
        items = toolbardata['ITEMS']
        gtk.Toolbar.__init__(self)
        self.buttons = []
        self.data = data 
        self.items = items
        for item in items:
            icon = gtk.Image()

            icon.set_from_file(self._getIconPath(item['icon']))
            self.buttons.append(self.append_item(item['name'],
                                                 item['tooltip'], 
                                                 "Private",
                                                 icon,
                                                 self.execAction,
                                                 item['action']
                                                 ))
            addEventsHandling(self.buttons[-1], item)
            self.buttons[-1].set_sensitive(item['sensitive'])
            
        self.set_style(gtk.TOOLBAR_BOTH)
        self.set_sensitive(toolbardata['sensitive'])

    def execAction(self, widget, actioncode):
        if 'topwindow' not in self.data:
            self.data['topwindow'] = self.get_parent_window()
        eval(compile(actioncode, "error.log", "exec"), globals(), self.data)

    def __getitem__(self, name):
        index = [i for i in range(len(self.items)) if self.items[i]['name']==name][0]
        return self.items[index]


class MenuBar(gtk.MenuBar):
    
    def __init__(self, menubardata, data={}):
        items = menubardata['ITEMS']
        gtk.MenuBar.__init__(self)
        self.data = data
        self.menus = [createInstance(Menu,item, data=data) for item in items]
        map(self.append, self.menus)
        self.set_sensitive(menubardata['sensitive'])
        
    def show(self):
        [m.show() for m in self.menus]
        gtk.MenuBar.show(self)
        
    def __getitem__(self, name):
        index = [i for i in range(len(self.menus)) if self.menus[i].name==name][0]
        return self.menus[index]
        

class Menu(gtk.MenuItem):
    
    def __init__(self, plugindata, data={}):
        name = plugindata['name']
        items = []
        if 'ITEMS' in plugindata: items = plugindata['ITEMS']
        gtk.MenuItem.__init__(self, name)
        self.items = items
        self.data = data

        self.menu = gtk.Menu()
        self.label = gtk.Label(name)
        self.label.set_use_underline(True)
        self.menu.add_mnemonic_label(self.label)
        self._setup()
        self.set_sensitive(plugindata['sensitive'])

    def _setup(self):
        items = self.items
        self.mitems = [createInstance(Menu, item, data=self.data) for item in self.items]
        for i in range(len(items)):
            mitem = self.mitems[i]
            self.menu.append(mitem)
            mitem.connect("activate", self.execAction, items[i]['action'])
            mitem.set_tooltip_text(items[i]['tooltip'])
            #mitem.set_use_underline(True)
            if "icon" in items[i]:
                img = gtk.Image()
                img.set_from_file(items[i]['icon'])
                mitem.set_image(img)
                img.show()
        if self.mitems:
            self.set_submenu(self.menu)

    def show(self):
        [item.show() for item in self.mitems]
        gtk.MenuItem.show(self)

    def __getitem__(self, name):
        index = [i for i in range(len(self.items)) if self.items[i]['name']==name][0]
        return self.mitems[index]
    
    def execAction(self, widget, actioncode):
        if 'topwindow' not in self.data:
            self.data['topwindow'] = self.get_parent_window ()
        self.data['multicaster'] = events.EventMulticaster()
        """
        for line in actioncode.split("\n"):
            exec line"""
        eval(compile(actioncode, "error.log", "exec"), globals(), self.data)

