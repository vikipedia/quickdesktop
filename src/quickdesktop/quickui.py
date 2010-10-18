import pygtk
import sys
import gtk
import threading
import gobject
import time
import re
import random
import os
from quickdesktop import events
from quickdesktop import configuration
from quickdesktop import common
from quickdesktop import const
from quickdesktop import resource

pygtk.require("2.0")

def getParentWindow(widget):
    """
    return toplevel gtk.Dialog or gtk.Window for given widget
    """
    if widget:
        t = type(widget)
        if t in [gtk.Dialog, gtk.Window]:
            return widget
        return getParentWindow(widget.get_parent())


def setIcon(window):
    """
    sets resource icon, 'resource:logo.xpm' to window decoration if exists.
    """
    try:
        icon = resource.getResource("resource:logo.xpm")
        if icon:
            window.set_icon_from_file(icon)
    except:
        pass
    

def showDialog(widget,title=None,parent=None,flags=0,buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OK, gtk.RESPONSE_OK)):
    """
    Most common way of showing widgets from quickui library.
    """
    d = gtk.Dialog(title=title, parent=parent,flags=False,buttons=buttons)
    d.vbox.pack_start(widget,True, True, 0)
    setIcon(d)

    widget.show()
    widget.fireValueChanged()
    
    while True:
        response = d.run()
        if response == gtk.RESPONSE_OK:
            try:
                v = widget.getValue()
                d.destroy()
                return v
            except ValueError, e:
                error(parent=d,message=e.message)
                continue
        else:
            d.destroy()
            return None

def error(parent=None, message=None):
    """
    Shows error dialog with message given as argument.
    """
    d = gtk.MessageDialog(parent=parent, type=gtk.MESSAGE_ERROR, message_format=message, buttons=gtk.BUTTONS_CLOSE)
    d.set_title("Error")
    setIcon(d)
    response = d.run()
    d.destroy()
    return response

def warning(parent=None, message=None):
    """
    Shows warning dialog with message given as argument.
    """
    d = gtk.MessageDialog(parent=parent, type=gtk.MESSAGE_WARNING, message_format=message, buttons=gtk.BUTTONS_CLOSE)
    d.set_title("Warning")
    setIcon(d)
    response = d.run()
    d.destroy()
    return response

def info(parent=None, message=None):
    """
    Shows info message dialog with message given as argument.
    """
    d = gtk.MessageDialog(parent=parent, type=gtk.MESSAGE_INFO, message_format=message, buttons=gtk.BUTTONS_CLOSE)
    d.set_title("Information")
    setIcon(d)
    response = d.run()
    d.destroy()
    return response


def question(parent=None, message=None):
    """
    Shows Yes/No question dialog with message given as argument.
    """
    d = gtk.MessageDialog(parent=parent, type=gtk.MESSAGE_QUESTION, message_format=message, buttons=gtk.BUTTONS_YES_NO)
    d.set_title("Question?")
    setIcon(d)
    response = d.run()
    d.destroy()
    return response

class QuickWidget(gtk.Widget):    
    """
    interface for quickui library
    """
    def __init__(self, quickid=None, description=None, value=None, validator=None, hideon=None):
        gtk.Widget.__init__(self)
        self.type = "QuickWidget"
        if not quickid:
            raise TypeError("quickid for QuickWidget can not be None")
        self.quickid = quickid
        self.description = description
        if description==None: self.description=quickid
        self.value = value
        self.validator = validator
        self.sensitive = True
        self.VALUE_CHANGED_EVENT = self._getValueChangedEventName(quickid)
        self.events = []
        self.hideon = hideon
        """
        if hideon:
            self.addListeners(hideon)
            """
    def _getValueChangedEventName(self, quickid):
        return "_".join([quickid, "VALUE_CHANGED"])

    def quickcleanup(self):
        for e in self.events:
            events.EventMulticaster().removeListener(e, self)

    def getValue(self):
        """
        Return value in the widget. Also calls validator before returning value.
        """
        if self.validator:
            self.validator(self.value)
        return self.value
 
    def fireValueChanged(self):
        events.EventMulticaster().dispatchEvent(self.VALUE_CHANGED_EVENT,
                                                {'type':self.VALUE_CHANGED_EVENT,
                                                 'origin':self,
                                                 self.quickid:self.value})
   
    def getType(self):
        return self.type

    def __getitem__(self, name):
        if name=="value":
            return self.getValue()
        return vars(self)[name]

    def __setitem__(self, name, value):
        vars(self)[name] = value

    def __repr__(self):
        return " : ".join([self.type, str(self.value)])

def runWithProgressDialog(parent,title,function,pulse=False,**kwargs):
    """
    Runs given function with progress dialog.
    Before using this function, make sure
    gtk.gdk.threads_init() must be called before gtk_init() in main loop.
    """
    
    dialog = gtk.Dialog(title=title, parent = parent)
    setIcon(dialog)
    b = gtk.Button(stock= gtk.STOCK_CANCEL)
    taskid = str(time.time()+random.random()) + function.func_name
    taskid = taskid.replace(".", "_")
    task = Task(taskid, function, **kwargs)
    progressbar = ProgressBar(taskid, title, pulse, task= task)

    class DoneListener:
        
        def __init__(self, dialog, task):
            self.dialog = dialog
            self.task = task

    code = """
listenerObject.dialog.destroy()
listenerObject.task.cleanup()
"""
    l = DoneListener(dialog, task)
    events.addEventListener(task.DONE_EVENT, l, code, {'e':events.EventMulticaster()})
    b.connect("clicked", lambda button, dialog, task: [task.abort(),dialog.destroy()], dialog, task)

    dialog.action_area.pack_start(b, True, False, 0)
    dialog.vbox.pack_start(progressbar, True, True, 0)

    progressbar.show()
    b.show()

    task.start()
    dialog.run()
    

class ProgressBar(QuickWidget, gtk.HBox):
    """
    Before using this class, make sure
    gtk.gdk.threads_init() must be called before gtk_init() in main loop.
    """
    def __init__(self, quickid, description=None,pulse=False, task=None, hideon=None):
        QuickWidget.__init__(self, quickid, description, None, None, hideon=hideon)
        gtk.HBox.__init__(self, True, 0)
        self.type = "ProgressBar"

        self.task = task
        self.pulse = pulse

        self.alignment = gtk.Alignment(0.5,0.5,1.0,1.0)
        self.progressbar = gtk.ProgressBar()

        if self.pulse:
            self.timer = gobject.timeout_add (100, lambda progressbar: gobject.idle_add(progressbar.pulse), self.progressbar)

        self.alignment.add(self.progressbar)
        self.pack_start(self.alignment, True, True, 0)
        self._setupEvents()
        
    def _setupEvents(self):
        self._setup_FRACTION_CHANGED_EVENT()
        self._setup_TEXT_CHANGED_EVENT()
        self._setup_DONE_ABORT_EVENTs()

    def _setup_FRACTION_CHANGED_EVENT(self):
        CODE = """
fraction = eventData['fraction']
listenerObject.set_fraction(fraction)
"""
        events.addEventListener(self.task.FRACTION_CHANGED_EVENT, self, CODE, {})

    def _setup_TEXT_CHANGED_EVENT(self):
        CODE = """
text = eventData['text']
listenerObject.set_text(text)
"""
        events.addEventListener(self.task.TEXT_CHANGED_EVENT, self, CODE, {})

    def _setup_DONE_ABORT_EVENTs(self):
        CODE = """
if listenerObject.pulse:
    gobject.source_remove(listenerObject.timer)
listenerObject.task.cleanup()
"""
        e = events.EventMulticaster()
        events.addEventListener(self.task.DONE_EVENT, self, CODE, {'e':e,'task':self.task, 'gobject':gobject})
        events.addEventListener(self.task.ABORT_EVENT, self, CODE, {'e':e,'task':self.task, 'gobject':gobject})


    def show(self):
        self.alignment.show()
        self.progressbar.show()
        gtk.HBox.show(self)

    def hide(self):
        self.alignment.hide()
        self.progressbar.hide()
        gtk.HBox.hide(self)

    def set_fraction(self, fraction):
        def _set_fraction(fraction):
            self.progressbar.set_fraction(fraction)
        gobject.idle_add(_set_fraction, fraction)
        
    def set_text(self, message):
        def _set_text(message):
            self.progressbar.set_text(message)
        gobject.idle_add(_set_text,message)

class Task(threading.Thread):
    
    RUNNING = "RUNNING"
    DONE = "DONE"
    ABORTED = "ABORTED"
    status = RUNNING

    def __init__(self, taskid ,function, **kwargs):
        threading.Thread.__init__(self)
        self.taskid = taskid
        self.kwargs = kwargs
        self.function = function
        self.FRACTION_CHANGED_EVENT = "_".join([self.taskid, "FRACTION_CHANGED"])
        self.DONE_EVENT = "_".join([self.taskid, "DONE"])
        self.ABORT_EVENT = "_".join([self.taskid, "ABORTED"])
        self.TEXT_CHANGED_EVENT = "_".join([self.taskid, "TEXT_CHANGED"])

    def run(self):
        print "running in new thread",self.function
        self.status = self.RUNNING
        self.function(task=self, **self.kwargs)
        print "finished execution"
        if self.status!=self.ABORTED:
            self.status = self.DONE
            events.EventMulticaster().dispatchEvent(self.DONE_EVENT, 
                                                    {'type':self.DONE_EVENT,
                                                     'origin':self})
    def isRunning(self):
        return self.status == self.RUNNING

    def cleanup(self):
        e = [self.ABORT_EVENT, self.FRACTION_CHANGED_EVENT, self.DONE_EVENT,self.TEXT_CHANGED_EVENT]
        emc = events.EventMulticaster()
        map(emc.removeAllListeners, e)
        
    def abort(self):
        if self.status!=self.DONE:
            self.status = self.ABORTED
            events.EventMulticaster().dispatchEvent(self.ABORT_EVENT, 
                                                    {'type':self.ABORT_EVENT,
                                                     'origin':self})
        
    def set_fraction(self, fraction):
        self.fraction = fraction
        events.EventMulticaster().dispatchEvent(self.FRACTION_CHANGED_EVENT, 
                                                {'origin':self,
                                                 'type':self.FRACTION_CHANGED_EVENT,
                                                 'fraction':fraction})
            
    def set_text(self, text):
        self.text = text
        events.EventMulticaster().dispatchEvent(self.TEXT_CHANGED_EVENT,
                                                {'origin':self,
                                                 'type':self.TEXT_CHANGED_EVENT,
                                                 'text':text})
class _Label(gtk.Alignment):
    
    def __init__(self, label):
        self.label = gtk.Label(label)
        self.label.set_justify(gtk.JUSTIFY_RIGHT)
        gtk.Alignment.__init__(self, 0.0,0.5,0.0,0.5)
        self.add(self.label)

    def show(self):
        self.label.show()
        #self.frame.show()
        gtk.Alignment.show(self)

    def hide(self):
        self.label.hide()
        #self.frame.hide()
        gtk.Alignment.hide(self)

    
    def set_sensitive(self, sensitive):
        self.label.set_sensitive(sensitive)
        gtk.HBox.set_sensitive(self, sensitive)
        #self.frame.set_sensitive(sensitive)

class String(gtk.HBox, QuickWidget):
    """
    Widget for taking string inputs
    """
    
    def __init__(self, quickid=None, description=None, value=None, maxlength=200, validator=lambda x:x, hideon=None, homogeneous=True):
        QuickWidget.__init__(self,quickid, description, value, validator, hideon=hideon)
        gtk.HBox.__init__(self, homogeneous, 0)
        self.type = "String"
        
        self.descriptionlabel = _Label(self.description)
        self.entry = gtk.Entry()
        self.entry.set_max_length(maxlength)
        self.entry.set_size_request(200,30)
        if value!=None: self.entry.set_text(value)
        
        events  = ['key-release-event']
        for e in events:
            self.entry.connect(e,self._valueChanged, e)
        self._setupComponents()

    def setSize(self, x,y):
        self.entry.set_size_request(x, y)

    def _setupComponents(self):
        self.pack_start(self.descriptionlabel,True,True,0)
        self.pack_start(self.entry, False, False, 0)
                
    def _valueChanged(self, entry, event,data):
        if self.validator:
            self.validator(entry.get_text())
        self.value = entry.get_text()
        self.fireValueChanged()

    def connect(self,*args, **kwargs):
        """
        connect to self.entry with various supported signals.
        """
        self.entry.connect(*args, **kwargs)
        
    def show(self):
        self.descriptionlabel.show()
        self.entry.show()
        gtk.HBox.show(self)

    def hide(self):
        self.descriptionlabel.hide()
        self.entry.hide()
        gtk.HBox.hide(self)
    
    def set_sensitive(self, sensitive):
        self.sensitive = sensitive
        self.entry.set_sensitive(sensitive)
        self.descriptionlabel.set_sensitive(sensitive)
      
    def set_editable(self, editable):
        self.entry.set_editable(editable)

    def setValue(self, value):
        """
        sets value in the entry and updates value.
        """
        if value!=None:
            self.entry.set_text(value)
        else:
            self.entry.set_text("")
        self._valueChanged(self.entry, None,None)
        
    def __setitem__(self, name, value):
        if name == "value":
            self.setValue(value)
        QuickWidget.__setitem__(self, name, value)

    
class Integer(String):
    """
    Quick widget for Integer inputs
    """
    
    def __init__(self, quickid=None, description=None, value=None, validator=None, maxvalue=None, minvalue=None, hideon=None, homogeneous=True):
        def f(x):
            if maxvalue!=None and x > maxvalue: 
                raise ValueError("Value of %s can not exceed %d"%(quickid,maxvalue))
            if minvalue!=None and x < minvalue:
                raise ValueError("Value of %s can not be less than %d"%(quickid,minvalue))
        if maxvalue < minvalue:
            raise ValueError("maxvalue has to be greater than or equal to minvalue.")
        validator = validator or f
        String.__init__(self,quickid,description,str(value),10,validator, hideon, homogeneous=homogeneous)
        self.value = int(value)
        self.type = "Integer"
        
        
    def _valueChanged(self, entry,event, data):
        value = int(self.entry.get_text())
        if self.validator:
            self.validator(value)
        self.value = value
        self.fireValueChanged()

    def setValue(self, value):
        self.entry.set_text(str(value))
        self._valueChanged(self, self.entry,None)
     
class Float(Integer):
    """
    Quick widget for float input
    """
    
    def __init__(self,quickid=None,description=None,value=None,validator=None,maxvalue=None,minvalue=None, hideon=None, homogeneous=True):
        Integer.__init__(self, quickid, description, value, validator, maxvalue, minvalue, hideon=hideon, homogeneous=homogeneous)
        self.type = "Float"
        self.value = float(value)

    def _valueChanged(self,entry,event,data):
        value = float(self.entry.get_text())
        if self.validator:
            self.validator(value)
        self.value = value
        self.fireValueChanged()

class Enum(gtk.HBox, QuickWidget):
    """
    Quick widget for choosing one item out of multiple options.
    """
    
    def __init__(self, quickid=None, description=None, value=None,options=None,validator=None, hideon=None):
        def validator(x):
            if x not in options:
                raise ValueError("Can not set value ",x)
            
        QuickWidget.__init__(self, quickid, description, value, validator, hideon=hideon)
        gtk.HBox.__init__(self, True, 0)
        self.type = "Enum"

        self.descriptionlabel = _Label(self.description)
        
        self.combobox = gtk.combo_box_new_text()
        self.combobox.set_size_request(200,30)
        self._populateitems(options, self.combobox)
   
        self.combobox.connect('changed', self._valueChanged)
        self.pack_start(self.descriptionlabel, True, True, 0)
        self.pack_end(self.combobox, False, False, 0)

    def _populateitems(self, options, combo):
        self.showitems = []
        self.comboitems = []
        
        if type(options)==type({}):
            for k,v in options.items():
                self.showitems.append(v)
                self.comboitems.append(k)
        else:
            self.showitems = [item for item in options]
            self.comboitems = self.showitems
            
        map(combo.append_text,self.showitems)
        if self.value!=None:
            combo.set_active(self.comboitems.index(self.value))
        
    def _valueChanged(self, combobox):
        model = combobox.get_model()
        index = combobox.get_active()
        if index>=0:
            index = self.showitems.index(model[index][0])
        if self.validator:
            self.validator(self.comboitems[index])
        self.value = self.comboitems[index]
        self.fireValueChanged()

    def setValue(self, v):
        self.combobox.set_active(self.comboitems.index(v))
        self._valueChanged(self.combobox)

    def __setitem__(self, name, value):
        if name == "value":
            self.setValue(value)
        QuickWidget.__setitem__(self, name, value)

    def connect(self, *args, **kwargs):
        """
        Connects various signals to combobox.
        """
        self.combobox.connect(*args, **kwargs)
        
    def show(self):
        self.descriptionlabel.show()
        self.combobox.show()
        gtk.HBox.show(self)
        
    def hide(self):
        self.descriptionlabel.hide()
        self.combobox.hide()
        gtk.HBox.hide(self)
        
    def set_sensitive(self, sensitive):
        self.sensitive = sensitive
        self.descriptionlabel.set_sensitive(sensitive)
        self.combobox.set_sensitive(sensitive)


class RadioButton(gtk.VBox,QuickWidget):

    def __init__(self, quickid=None, description=None, value=None,options=None,validator=None, hideon=None):
	
	QuickWidget.__init__(self, quickid, description, value, validator, hideon=hideon)
	gtk.VBox.__init__(self, True, 10)
        self.type = "RadioButton"

        self.descriptionlabel = _Label(self.description)
	self._populateitems(options)
	self.radioB=[gtk.RadioButton(None,self.showitems[0])]

        self.radioB[0].connect('toggled', self._valueChanged, self.valueitems[0])
        self.pack_start(self.descriptionlabel, True, True, 0)
        self.pack_end(self.radioB[0], False, False, 0)

	for i in range(len(self.showitems))[1:]:
	   s,r = self.showitems[i], self.valueitems[i]
	   self.radioB.append(gtk.RadioButton(self.radioB[i-1],s))
           self.radioB[i].connect('toggled', self._valueChanged, r)
           self.pack_end(self.radioB[i], False, False, 0)

	if value != None: self._selectRadio(value)

    def _selectRadio(self,v): 
	   for i in range(len(self.valueitems)):
		if v == self.valueitems[i]:
		    self.radioB[i].set_active(True)
		    break

    def _populateitems(self,option):
	self.showitems = []
	self.valueitems= []
	  
	if type(option) == type({}):        
            for k,v in option.items():
                self.showitems.append(v)
                self.valueitems.append(k)
        else:
            self.showitems = [item for item in options]
            self.valueitems = self.showitems
 

    def _valueChanged(self,radio,v):
        if self.validator:
            self.validator(v)
        self.value = v
        self.fireValueChanged()

    def setValue(self, value):
	self._valueChanged(None,value)
	self._selectRadio(value)
	self.value=value
        self.fireValueChanged()

    def show(self):
        self.descriptionlabel.show()
	for i in range(len(self.showitems)):
           self.radioB[i].show()
        gtk.VBox.show(self)

    def hide(self):
        self.descriptionlabel.hide()
	for i in range(len(self.showitems)):
           self.radioB[i].hide()
        gtk.VBox.hide(self)
        
    def set_sensitive(self, sensitive):
        self.sensitive = sensitive
        self.descriptionlabel.set_sensitive(self, sensitive)
	for i in range(len(self.showitems)):
           self.radioB[i].set_sensitive(self, sensitive)


class Table(gtk.VBox, QuickWidget):    
    """
    Simple table UI. To be used only for small tables. it is not a spreadsheet!
    """
    def __init__(self, quickid=None, description=None, columnnames=[], value=[], validator=None, hideon=None, selection="single"):
        """
        quickid = quick id of the widget.
        description = description if any
        columnnames = list of column names
        value = list of rows. for example for value=[[1,'a'],[2,'b']], [1,'a'] is first row in the table
        """

        QuickWidget.__init__(self,quickid, description, value, validator, hideon=hideon)
        self.type = "Table"
        gtk.VBox.__init__(self, False, 0)
        self.columnnames = columnnames
        self.columncount = len(columnnames)
        x = {'single':gtk.SELECTION_SINGLE, 'multi':gtk.SELECTION_MULTIPLE}
        self.selectionmode = x[selection]
        self._setupWidgets()
	self.treeview.set_size_request(300,200)


    def _setupWidgets(self):
        self.scrolledwindow = gtk.ScrolledWindow()
        self.model = gtk.ListStore(*[gobject.TYPE_STRING for i in range(self.columncount)])

        for row in self.value:
            self.model.append(row)
            
        self.treeview = gtk.TreeView(self.model)
            
        self.treecolumns = [gtk.TreeViewColumn(name) for name in self.columnnames]
        self.cells = [gtk.CellRendererText() for i in range(self.columncount) ]

        for i in range(self.columncount):
            c = self.treecolumns[i]
            self.treeview.append_column(c)
            c.pack_start(self.cells[i], True)
            c.add_attribute(self.cells[i], 'text', i)
            c.set_sort_column_id(i)

        self.treeview.set_reorderable(False)
	self.treeview.set_rules_hint(True)
        self.scrolledwindow.add(self.treeview)
        self.pack_start(self.scrolledwindow, True, True, 0)
        self.treeview.get_selection().set_mode(self.selectionmode)

    def setValue(self, value):
        if self.validator:
            self.validator(value)

        self.model.clear()

        for row in value:
            self.model.append(row)

        self.value = value
        self.fireValueChanged()

    def setSelection(self, selected):
        """
        set selection to given row indices.
        """
        selection = self.treeview.get_selection()
        selection.unselect_all()
        for item in selected:
            selection.select_path(item)

    def getSelection(self):
        selection = self.treeview.get_selection()
        if self.selectionmode == gtk.SELECTION_MULTIPLE:
            model, pathlist = selection.get_selected_rows()
            itr = [self.model.get_iter(i[0]) for i in pathlist]
            return [self.model.get_value(i, 0) for i in itr]
        model, itr = selection.get_selected()
        return [model.get_value(itr,0)]

    def show(self):
        gtk.VBox.show(self)
        self.scrolledwindow.show()
        self.treeview.show()

    def hide(self):
        gtk.VBox.hide(self)
        self.scrolledwindow.hide()
        self.treeview.hide()
        
    def set_sensitive(self, sensitive):
        self.sensitive = sensitive
        self.treeview.set_sensitive(sensitive)


class ListPair(gtk.HBox,QuickWidget):
    """
    An interface for pairing between two lists.
    """
    def __init__(self, quickid=None, description=None, value=None,validator=None,list1=[],list2=[], name1=None, name2=None, hideon=None, selection="single"):
        """
        quickid = quickid
        description = description
        list1 = list of values from first list.
        list2 = list of values from second list.
        name1 = name of first list.
        name2 = name of seconf list.
        value = default values to be passed as 2D list.
        selection = "multi" or "single" , default is "single"
        """
	
	QuickWidget.__init__(self, quickid, description, value, validator, hideon=hideon)

        self.value = value or [[item, None] for item in list1]
	self.list1 = list1
	self.list2 = list2
        self.name1 = name1
        self.name2 = name2 
        self.selection = selection

	gtk.HBox.__init__(self, False, 0)
	self.type="ListPair"

        self._createTables()

	self.pack_start(self.listL,False,5)
	self.pack_start(self.listR,False,5)
	self._create_entry()
	self._create_button()


    def _createTables(self):
	self.listL = Table(quickid="listL", description="", value=self.value, columnnames=[self.name1, self.name2], selection="multi")
	self.listR = Table(quickid="listR", description="", value=[[v] for v in self.list2], columnnames=[self.name2], selection=self.selection)


    def _create_entry(self):
	self.Lbox=gtk.HBox(False,0)
	self.listL.pack_start(self.Lbox,False,15)

	self.entry=gtk.Entry()
	self.Lbox.pack_start(self.entry,False,15)

        self.resetButton = gtk.Button("Reset")
        self.Lbox.pack_end(self.resetButton, False,15)
        self.resetButton.connect("clicked", self.resetSelected, None)
	self.entry.connect("key-release-event",self._searchSelect,None)

    def resetSelected(self, button, data=None):
	selectionL=self.listL.getSelection()
        value = self.getValue()
        firstcolumn = [v[0] for v in value]
        for i in selectionL:
            value[firstcolumn.index(i)][1] = None
        self.value = value
        self.listL.setValue(value)
        self.fireValueChanged()

    def _create_button(self):
	self.Rbox=gtk.HBox(False,0)
	self.listR.pack_start(self.Rbox,False,15)

	self.button=gtk.Button(stock='gtk-apply')
	self.Rbox.pack_end(self.button,False,15)
	self.button.connect("clicked",self._onApply,None)

	
    def _onApply(self,button,data=None):

	selectionL=self.listL.getSelection() 
	selectionR=self.listR.getSelection() 
        
        value = self.listL.getValue()
        leftcolumn = [v[0] for v in value]
        rightcolumn = [v[0] for v in self.listR.getValue()]
	for i in selectionL:
            v = [self.list2[rightcolumn.index(j)] for j in selectionR]
            value[leftcolumn.index(i)][1] = ListValue(v)
            

        self.listL.setValue(value)
        self.value = value
        self.fireValueChanged()

    def _searchSelect(self,entry,event, data=None):
	entry_text=entry.get_text()
        if not entry_text: return
	try:
            treeselection = self.listL.treeview.get_selection()
            p=re.compile(entry_text)
            treeselection.unselect_all()
            for i in range(len(self.list1)):
                if re.match(p, self.list1[i]):
                    treeselection.select_path(i)
        except:
            pass

    def show(self):
	self.entry.show()
	self.button.show()
	self.Lbox.show()
	self.Rbox.show()
        self.listL.show()
        self.listR.show()
        self.resetButton.show()
	gtk.HBox.show(self)


    def hide(self):
	self.entry.hide()
	self.button.hide()
	self.Lbox.hide()
	self.Rbox.hide()
        self.listL.hide()
        self.listR.hide()
        self.resetButton.hide()
	gtk.HBox.hide(self)

        
    def set_sensitive(self, sensitive):
	self.sensitive = sensitive
	self.listL.set_sensitive(self, sensitive)
	self.listR.set_sensitive(self, sensitive)


class PairingInterface(ListPair):
    """
    widget for pairing interfaces... inherits ListPair class
    """

    def __init__(self, quickid=None, description=None, value=None,validator=None,options=None, hideon=None):
        """
        quickid = quickid
        description = description
        options = list of values to be paired among themselves.
        value = default values to be passed as 2D list.
        """

	QuickWidget.__init__(self, quickid, description, value, validator, hideon=hideon)
        if value:
            self.value = [ListValue(r) for r in value]
	ListPair.__init__(self, quickid=quickid, description=description, value=value, validator=validator, list1=options, list2=options, name1=description, name2=description, hideon=hideon)
	self.type="PairingInterface"
        self.options = options

    def resetSelected(self, button, data=None):
        selectionL = self.listL.getSelection()
        value = self.getValue()
        firstcolumn = [v[0] for v in value]
        for i in selectionL:
            v = [item for item  in value[firstcolumn.index(i)][1]]
            value[firstcolumn.index(i)][1] = None
            for j in v:
                value[firstcolumn.index(j)][1].remove(i)
        self.value = value
        self.listL.setValue(value)
        self.fireValueChanged()

    def _createTables(self):
	self.listL = Table(quickid="listL", description="", value=self.value, columnnames=[self.name1, "Paired With"], selection="multi")
	self.listR = Table(quickid="listR", description="", value=[[v] for v in self.list2], columnnames=[self.name2], selection="multi")

    def _onApply(self, button, data=None):

        selectionL = self.listL.getSelection() #multiple selection
        selectionR = self.listR.getSelection() #multiple selection
        leftcolumn = [v[0] for v in self.listL.getValue()]
        rightcolumn = [v[0] for v in self.listR.getValue()] 
        rvlist = []
        for litem in selectionL:
            l = leftcolumn.index(litem)
            for ritem in selectionR:
                r = rightcolumn.index(ritem)
                v = []
                if self.value[l][1]:
                    v = [item for item in self.value[l][1]]
                rv = self.options[r]
                if rv not in v and rv!=self.options[l]:
                    v.append(rv)
                    rvlist.append((rv, self.options[l]))
                self.value[l][1] = ListValue(v)

        for r,l in rvlist:
            index = self.options.index(r)
            v = []
            if self.value[index][1]:
                v = [i for i in self.value[index][1]]
            if l not in v:
                v.append(l)
            self.value[index][1] = ListValue(v)

        self.listL.setValue(self.value)
        self.fireValueChanged()

class Boolean(gtk.CheckButton, QuickWidget):
    """
    Quickwidget for Boolean style values. Checkbox is used to represent boolean
    values.
    """

    def __init__(self, quickid=None, description=None, value=None,validator=None, hideon=None):
        QuickWidget.__init__(self, quickid, description, value, validator,hideon=hideon)
        gtk.CheckButton.__init__(self, description or quickid)
        self.type = "Boolean"
        self.connect("toggled",self._valueChanged)
        self.set_active(value)

    def _valueChanged(self,widget):
        if self.validator:
            self.validator(widget.get_active())
        self.value = widget.get_active()
        self.fireValueChanged()
    
    def setValue(self,value):
        self.set_active(value)
        self._valueChanged(self)

    def __setitem__(self, name, value):
        if name=="value":
            self.setValue(value)
        QuickWidget.__setitem__(self, name, value)

    def set_sensitive(self):
        self.sensitive = sensitive
        gtk.CheckButton.set_sensitive(self, sensitive)
        
class QFileChooser(String):
    """
    Quick widget from choosing/saving a file/directory
    """
    
    def __init__(self, quickid=None, description=None, value=None,validator=None,action="fileopen",filefilter=("All Files", "*.*"),multi=False, hideon=None):
        """
        actions supported
        fileopen - open an existing file
        filesave - save a new file
        diropen - open an existing directory
        dirsave - create a new directory

        filefilter - tuple of filter name and allowed regex inf ile names
        default filefilter -> All Files "*.*"
        """
        self.ACTIONS = {
            "fileopen" : gtk.FILE_CHOOSER_ACTION_OPEN,
            "filesave" : gtk.FILE_CHOOSER_ACTION_SAVE,
            "diropen"  : gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
            "dirsave"  : gtk.FILE_CHOOSER_ACTION_CREATE_FOLDER
            }

        self.multi = multi
        self.selectbutton = gtk.Button("Browse...")
        self.selectbutton.connect("clicked",self.showDialog,filefilter,self.ACTIONS[action],self.multi)
        String.__init__(self, quickid, description, value, 200, validator, hideon=hideon)
        self.type = "QFileChooser"

    def _setupComponents(self):
        self.pack_start(self.descriptionlabel, True, True, 0)
        self.hbox2 = gtk.HBox()
        self.hbox2.pack_start(self.entry, True, False, 0)
        self.hbox2.pack_start(self.selectbutton,False, False,0)
        self.pack_start(self.hbox2, False, False, 0)
        
    def show(self):
        gtk.HBox.show(self)
        self.hbox2.show()
        self.descriptionlabel.show()
        self.entry.show()
        self.selectbutton.show()

    def hide(self):
        gtk.HBox.hide(self)
        self.hbox2.hide()
        self.descriptionlabel.hide()
        self.entry.hide()
        self.selectbutton.hide()

    def set_sensitive(self, sensitive):
        String.set_sensitive(self, sensitive)
        self.descriptionlabel.set_sensitive(sensitive)
        self.entry.set_sensitive(sensitive)
        self.selectbutton.set_sensitive(sensitive)

    def _getFileFilter(self, filefilter):
        f = gtk.FileFilter()
        f.set_name(filefilter[0])
        [f.add_pattern(p) for p in filefilter[1:]]
        return f

    def _createFileChooser(self,filefilter, action):
        filefilter = self._getFileFilter(filefilter)
        parent = getParentWindow(self)
        self.filechooser = gtk.FileChooserDialog(title ="Open...",
                                                 parent = parent,
                                                 action = action,
                                                 buttons = (gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        setIcon(self.filechooser)
        self.filechooser.set_default_response(gtk.RESPONSE_OK)
        self.filechooser.add_filter(filefilter)

        if self.value:
            import os
            self.currentfolder = os.path.dirname(self.value)
            self.filechooser.set_current_folder(self.currentfolder)
            if action in [gtk.FILE_CHOOSER_ACTION_CREATE_FOLDER,gtk.FILE_CHOOSER_ACTION_SAVE]:
                self.filechooser.set_current_name(os.path.basename(self.value))
        
    def showDialog(self,widget,filefilter,action,multi):
        """
        Shows file chooser dialog.
        """
        self._createFileChooser(filefilter , action)
        response = self.filechooser.run()
        if response == gtk.RESPONSE_OK:
            v = self.filechooser.get_filename()
            self.setValue(v)
        self.filechooser.destroy()

class Matrix(gtk.VBox, QuickWidget):
    
    def __init__(self, quickid=None, description=None, options=[], value=None, hideon=None, validator=None):
        gtk.VBox.__init__(self, False, 2)
        QuickWidget.__init__(self, quickid=quickid, description=description, value=value, hideon=hideon, validator=validator)
        type="Matrix"
        self.options = options
        self._setupMatrix()
        
    def _setupMatrix(self):
        self.floatwidgets = []
        self.vbox = []
        self.descriptionlabel = _Label(self.description)
        self.vbox.append(gtk.VBox(False, 0))
        self.vbox[-1].pack_start(self.descriptionlabel, False, False, 0)
        self.pack_start(self.vbox[-1], False, False, 0)
        
        self.hbox = gtk.HBox(False, 0)
        for i in range(len(self.options)):#rows
            r = []
            self.vbox.append(gtk.VBox(False, 2))
            for j in range(len(self.options[i])):#columns
                r.append(createWidget(type="Float", quickid=str((i,j)), description=self.options[i][j], value=self.value[i][j], homogeneous=False))
                r[-1].setSize(100, 30)
                r[-1].connect("key-release-event", self._valueChanged, (i,j))
                self.vbox[-1].pack_start(r[-1], False, False, 0)
            self.hbox.pack_start(self.vbox[-1],False, False, 5)
            self.floatwidgets.append(r)
        self.pack_start(self.hbox, False, False, 0)

    def _valueChanged(self, entry, event, position):
        value = float(entry.get_text())
        if self.validator:
            self.validator(value)
        self.value[position[0]][position[1]] = value
        self.fireValueChanged()
        
    def setValue(self, value):
        for i in range(len(value)):
            for j in range(len(value[i])):
                if self.validator:
                    self.validator(value[i][j])
                self.floatwidgets[i][j].setValue(value[i][j])
        self.value = value
        self.fireValueChanged()

    def show(self):
        [h.show() for h in self.vbox]
        [[i.show() for i in row] for row in self.floatwidgets]
        gtk.VBox.show(self)
        self.hbox.show()
        self.descriptionlabel.show()

    def hide(self):
        [h.hide() for h in self.vbox]
        [[i.hide() for i in row ] for row in self.floatwidgets]
        gtk.VBox.hide(self)
        self.hbox.hide()
        self.descriptionlabel.hide()


class Group(gtk.VBox, QuickWidget):
    
    def __init__(self, quickid=None,description=None, components=[], showBorder=False, addSeperator=False, hideon=None):
        QuickWidget.__init__(self, quickid=quickid, description=description, value=None, hideon=hideon)
        self.type = "Group"
        self.components = components
        self.showBorder = showBorder
        self.addSeperator = addSeperator

        gtk.VBox.__init__(self, True, 0)
        self._createVbox()
        self._setLayout()

    def _setLayout(self):
        if self.showBorder:
            self.frame = gtk.Frame(self.description)
            self.frame.add(self.vbox2)
            gtk.VBox.pack_start(self, self.frame, False, False, 0)
        else:
            gtk.VBox.pack_start(self, self.vbox2, False, False, 0)

        self.vbox2.set_border_width(10)


    def _createVbox(self):
        self.vbox2 = gtk.VBox()
        self.sep = []

        for i in range(len(self.components)-1):

            self.vbox2.pack_start( self.components[i], False, False, 2)
            if self.addSeperator:
                self.sep.append(gtk.HSeparator())
                self.vbox2.pack_start(self.sep[-1], False, False, 0)
        self.vbox2.pack_start(self.components[-1], False, False, 2)

    def getValue(self):
        """
        Returns current selection in combobox.
        """
        self.value = {}
        for c in self.components :
            if c.sensitive: self.value[c['quickid']] = c['value']
        return self.value

    def show(self):
        self.vbox2.show()
        if self.showBorder:
            self.frame.show()
        for c in self.components:
            c.show()
        for s in self.sep:
            s.show()
        gtk.VBox.show(self)

    def connect(self, quickid, *args, **kwargs):
        for c in self.components:
            if c.quickid==quickid:
                c.connect(*args, **kwargs)

    def hide(self):
        self.vbox2.hide()
        if self.showBorder:
            self.frame.hide()
        for c in self.components:
            c.hide()
        for s in self.sep:
            s.hide()
        gtk.VBox.hide(self)


    def set_sensitive(self, sensitive):
        self.sensitive = sensitive
        for c in self.components:
            c.set_sensitive(sensitive)
    
    def __getitem__(self, name):
        if name=="value":
            return self.getValue()
        return QuickWidget.__getitem__(self, name)
    
    def quickcleanup(self):
        for c in self.components:
            c.quickcleanup()
        QuickWidget.quickcleanup(self)
        
    def fireValueChanged(self):
        for c in self.components:
            c.fireValueChanged()
        QuickWidget.fireValueChanged(self)

class Custom(QuickWidget, gtk.EventBox):
    """
    QuickWidget for showing any customised widget. 
    This just puts a QuickWidget wrapper over any gtk widget.
    """
    def __init__(self, quickid=None, description=None, value=None, component=None, hideon=None):
        QuickWidget.__init__(self, quickid=quickid, description=description, value=value, hideon=hideon)
        gtk.EventBox.__init__(self)
        self.type = "Custom"
        self.component = component
        gtk.EventBox.add(self, self.component)


    def getValue(self):
        return None
        
    def show(self):
        self.component.show()
        gtk.EventBox.show(self)

    def hide(self):
        self.component.hide()
        gtk.EventBox.hide(self)

    def set_sensitive(self, sensitive):
        self.sensitive = sensitive
        self.component.set_sensitive(sensitive)

    def connect(self, *args, **kwargs):
        self.component.connect(*args, **kwargs)

class ScrolledWidget(QuickWidget, gtk.ScrolledWindow):
    
    def __init__(self, widget=None):
        QuickWidget.__init__(self, quickid=widget.quickid, description=widget.description, value=widget.value)
        gtk.ScrolledWindow.__init__(self)
        self.type = "ScrolledWidget"
        self.widget = widget
        self.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.add_with_viewport(widget)
        self.set_border_width(10)
    
    def getValue(self):
        return self.widget.getValue()

    def show(self):
        gtk.ScrolledWindow.show(self)
        self.widget.show()

    def hide(self):
        gtk.ScrolledWindow.hide(self)
        self.widget.hide()
    
    def set_sensitive(self, sensitive):
        self.sensitive = sensitive
        gtk.ScrolledWindow.set_sensitive(self, sensitive)
        self.widget.set_sensitive(sensitive)

def createWidget(**args):
    """
    main method to create quick widgets quickly. As of now it supports following types of widgets
    String
    Integer
    Float
    Boolean
    QFileChooser
    Enum
    Group
    Custom
    """
    widgettype = args['type']
    del args['type']
    return eval("%s(**args)"%(widgettype),globals(), locals())


def createLayout(layout, widgets):
    if layout:
        nb = gtk.Notebook()
        nb.set_tab_pos(gtk.POS_TOP)
        for label in layout.keys():
            l = gtk.Label(label)
            wl = [widgets[i] for i in layout[label]]
            c = createWidget(quickid=label, type="Group", components=wl)
            c.show()
            l.show()
            nb.append_page(c, l)
        return createWidget(quickid="layout", type="Custom", component=nb)
    else:
        return createWidget(quickid="layout", type="Group", components=widgets.values())

class ConfigTree(gtk.HPaned):
    
    def __init__(self, tree, title, savespace=None):
        self.tree = tree
        self.title = title
        self.confmanager = configuration.ConfigurationManager(savespace=savespace)
        gtk.HPaned.__init__(self)
        self._setupWidgets()

    def _setupWidgets(self):
        self.treescroll = gtk.ScrolledWindow()
        self.components = {}
        self._setupTree()
        self.treescroll.add(self.treewidget)
        self.add1(self.treescroll)
        self.vbox = gtk.VBox(True, 10)
        self.add2(self.vbox)
        self._createConfigUI()

    def addValueChangeListeners(self):
        code = """
def getEnv(components):
    values = {}
    for c in components:
        values.update(c.getValue())

    return values
            
env = getEnv(listenerObject.components.values())

for item in listenerObject.components.values():
    for c in item.components:
        if c.hideon:
            if eval(c.hideon,env, env):
                c.hide()
            else:
                c.show()
"""
        self.events = []
        expr = re.compile("([\w\-_]+)[!=<>]{1,2}.*")
        for item in self.components.values():
            for c in item.components:
                if c.hideon:
                    
                    items = c.hideon.split(" or ")
                    for i in items:
                        i = i.strip()
                        m = re.match(expr, i)
                        qid = m.groups()[0]
                        EVENT = c._getValueChangedEventName(qid)
                        events.addEventListener(EVENT, self, code, {})
                        self.events.append(EVENT)

        
    def reload(self):
        for item in self.components.keys():
            self.confmanager.discard(item)

        self.clearcomponents()
        self._createConfigUI()
        item = self.getSelectedItem()
        self.components[item].show()
        self.fireValueChanged()


    def _setupTree(self):
        self.treestore = self._createTreeStore(self.tree)
        self.treewidget = gtk.TreeView(self.treestore)
        self.treewidget.expand_all()
        self.tvcolumn = gtk.TreeViewColumn(self.title)
        self.treewidget.append_column(self.tvcolumn)
        self.cell = gtk.CellRendererText()
        self.tvcolumn.pack_start(self.cell, True)
        self.tvcolumn.add_attribute(self.cell, 'text', 0)
        self.treewidget.set_search_column(0)
        self.tvcolumn.set_sort_column_id(0)
        self.treewidget.set_reorderable(False)
        self.treewidget.connect("cursor-changed", self.showConfigItem)

    def _createConfigUI(self):
        def createConfigUI(tree, components):
            if type(tree)==type([]):
                [createConfigUI(node, components) for node in tree[1:]]
            else:
                components[tree] = createConfigWidget(tree, savespace=self.confmanager.savespace)

        createConfigUI(self.tree, self.components)
        for c in self.components.values():
            self.vbox.pack_start(c, False, False, 0)
        self.addValueChangeListeners()

    def showConfigItem(self, treeview):
        item = self.getSelectedItem()
        for i in self.components.keys():
            if item==i:
                self.components[i].show()
            else:
                self.components[i].hide()

        self.fireValueChanged()

    def fireValueChanged(self):
            for c in self.components.values():
                c.fireValueChanged()

    def _createTreeStore(self, tree):
        def addItem(store, itr, item):
            if type(item)==type([]):
                _itr = store.append(itr, [item[0]])
                for i in item[1:]:
                    addItem(store, _itr, i)
            else:
                store.append(itr, [item])

        treestore = gtk.TreeStore(str)
        addItem(treestore, None, tree)
        return treestore

    def show(self):
        gtk.HPaned.show(self)
        self.treescroll.show()
        self.vbox.show()
        self.treewidget.show()

    def onApply(self):
        for k, v in self.components.items():
            self.confmanager.save(k, v.getValue())

    def getSelectedItem(self):
        treeselection = self.treewidget.get_selection()
	model, itr = treeselection.get_selected()
        if itr:
            return model.get(itr, 0)[0]
            
    def reloadSelected(self):
        item = self.getSelectedItem()
        if item:
            self.confmanager.discard(item)
            self.vbox.remove(self.components[item])
            self.components[item] =  createConfigWidget(item, savespace=self.confmanager.savespace)
            self.vbox.pack_start(self.components[item], False, False, 0)
            self.components[item].show()
            self.fireValueChanged()

    def cleanup(self):
        em = events.EventMulticaster()
        for e in self.events:
            em.removeListener(e, self)

    def clearcomponents(self):
        for itemname,item in self.components.items():
            self.vbox.remove(item)
            del self.components[itemname]

class ListValue(list):

   def __init__(self, iterable):
	list.__init__(self, iterable)
            
   def __repr__(self):
        return ",".join([str(i) for i in self])

def createConfigWidget(confid, savespace):
    conf = configuration.getConfiguration(confid, savespace)
    items = conf['ITEMS']
    components = [createWidget(**i) for i in items]
    return createWidget(quickid=confid, type="Group", components=components)
    
def showConfigurationTree(title="Configuration Tree",parent=None, tree=None, savespace=None, button=(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)):
    ct = ConfigTree(tree, title, savespace=savespace)
    buttons = (button[0], button[1],
               gtk.STOCK_APPLY, gtk.RESPONSE_APPLY,
               "Default-All", gtk.RESPONSE_NONE,
               "Default", gtk.RESPONSE_REJECT)
    dialog = gtk.Dialog(title=title, parent=parent, flags=False, buttons=buttons)
    dialog.set_size_request(700,500)
    ct.set_position(250)
    setIcon(dialog)
    dialog.vbox.pack_start(ct, True, True, 0)
    ct.show()

    while True:
        response = dialog.run()
        if response == gtk.RESPONSE_APPLY:
            try:
                ct.onApply()
            except ValueError, e:
                error(parent=dialog,message=e.message)
                continue
        elif response == gtk.RESPONSE_REJECT:
            ct.reloadSelected()
        elif response == gtk.RESPONSE_NONE:
            ct.reload()
        else:
            ct.cleanup()
            dialog.destroy()
            return response


def testProgress(start=0, end=10, task=None):
    i = start
    task.set_text("Calculating...")
    while task.isRunning() and i < (end-start):
        [j*j for j in range(500000)]
        f = 1.0*(i+1)/(end-start)
        task.set_fraction(f)
        task.set_text("Done " + str(f*100) + "%")
        i = i +1
        

def testConfig():
    const.home = "/home/vikrant/programming/work/rep/sample"
    try:
        os.mkdir(const.home + "/test1")
    except:
        pass
    #w = createConfigWidget("sample")
    #showDialog(w)
    t = common.parseTree(const.home+"/config/tree.txt")
    showConfigurationTree(tree=t, savespace=const.home + "/test1")

if __name__=="__main__":

    c = createWidget(type="Table", quickid='t', description="s",columnnames=['a','b','c'], value=[['a1','a2asdasdasd','r'],['b1','b2asdasdasd','q'],['c1','c2dasdasdsadasd','p']])
    #c = createWidget(type="ListPair", quickid="t", description="sd", list1=['aSAS','basdas','csadasd','sdasdfyfusdy','iudkjfhsd'], list2=['pasdas','qasdas','rsdasd'], name1="ABC", name2="PQR") 
    #c = createWidget(type="PairingInterface", quickid="t", description="Interfaces", options=['aasdasd','basdasd','vdasdfdsf']) 
    showDialog(c)
    print c.getValue()
    dom

    #testConfig()
    #dom
    #Sample code starts here
    #runWithProgressDialog(None, "Test", testProgress,pulse=False,start=0, end=1000)
    s0 = createWidget(type="Matrix", quickid="m", description="Matrix", value=[[1.0,2.0],[3.0,4.0]], options=[['abcsdasas asa','b'],['','dasasas as->']])

    s1 = createWidget(type="String", quickid="name",description="",value="testxxx", maxlength=10)
    s2 = createWidget(type="Integer",quickid="x",description="Some Integer",value=5, maxvalue=10)
    s3 = createWidget(type="Float",quickid="y",description="1.5 <= Float <= 100.5",value=10.0, maxvalue=100.5, minvalue=1.5)
    s4 = createWidget(quickid="z",type="Float",value=10.0, maxvalue=100.5, minvalue=1.5)
    s5 = createWidget(type="Enum",quickid="p",options={'a':"Asdsfdfdsfdsfdsfdsfds",'b':"B",'c':"C"}, value="c")
    g1 = createWidget(type="Group",quickid="a",components=[s0, s1,s2,s3,s4,s5])

    s1 = createWidget(type="String",quickid="bx",description="Another String",value="testxxx", maxlength=10)
    s2 = createWidget(type="Integer",quickid="by",description="Yet another integer with too long description",value=5, maxvalue=10)
    s5 = createWidget(type="Enum",quickid="bz",options={'a':"Asdsfdfdsfdsfdsfdsfds",'b':"B",'c':"C"}, value="c")
    s5.setValue("b")
    s6 = createWidget(type="Boolean",quickid="bp",description="Select this", value=True)
    s7 = createWidget(type="QFileChooser",quickid="file",description="Choose file", value="/home/vikrant/examples.desktop", hideon="bp==False")

    task = Task("test", testProgress, start=0,end=5)
    s8 = createWidget(type="ProgressBar", quickid="progress", description="",task=task)
    
    #s6.connect("toggled",lambda w1,w2: w2.set_sensitive(w1.getValue()), s7)
    
    g2 = createWidget(type="Group",quickid="b",components=[s1,s2,s5,s6,s7,s8])
    g = createWidget(type="Group", quickid="z",components=[g1,g2],addSeperator=True)
    task.start()
    print showDialog(g,title="Quick Demo")
    print events.EventMulticaster().listeners
    
