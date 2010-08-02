import pygtk
import sys
import gtk
import os
import gobject
from quickdesktop import const
from quickdesktop import quickui
pygtk.require("2.0")

class _WizardProgress(gtk.HBox):
    
    def __init__(self):
        gtk.HBox.__init__(self, True, 0)
        self.alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        self.progressbar = gtk.ProgressBar()
        
        self.alignment.add(self.progressbar)
        self.pack_start(self.alignment, True, True, 0)
        
    def show(self):
        gtk.HBox.show(self)
        self.alignment.show()
        self.progressbar.show()

    def set_fraction(self, f):
        gobject.idle_add(lambda fraction: self.progressbar.set_fraction(fraction), f)

    def set_text(self, text):
        gobject.idle_add(lambda t: self.progressbar.set_text(t), text)

class _Wizard:
    """
    Class for Wizard. For complicated user inputs it is difficult to take
    all the inputs on a single input dialog. Wizard is remeady for such kind
    of requirement. Wizard displays series of GUI pages in certain sequence.
    At end it returns user inputs collected through the wizard.
    """
    
    def  __init__(self, title, wizpages,floworder,inputs, parent=None):
        """
        title - title of wizard
        wizpages - list of "Wizpage"
        floworder - flow order for pages. for example see samplewizard.py
        inputs - dictionary of inputs required for the wizard. these inputs 
        will be available as state inside wizard.
        """
        self.parent = parent
        self.pageids = [p.pageid for p in wizpages]
        self.pages = self._createDict(wizpages)
        self.floworder = floworder
        self.state = dict(inputs)
        self.output = {}
        self.title = title
        self.current = None
        self.history = []
        self._setup()
        self.state['parent'] = self.dialog

    def _createDict(self, pages):
        d = {}
        for p in pages:
            d[p.pageid] = p
        return d

    def _get_fraction(self):
        return 1.0*(self.pageids.index(self.current))/len(self.pageids)        

    def _get_text(self):
        return str(round(self._get_fraction()*100)) + "% Done"

    def _get_title(self):
        p = self.pages[self.current]
        index = self.pageids.index(self.current)+1
        return self.title + " - " + p.title + " %d/%d"%(index,len(self.pageids))

    def _setup(self):
        """
        Setting it up
        """
        self.current = self.floworder["*"][0][0] #start
        self.dialog = gtk.Dialog(title=self._get_title(), parent=self.parent)
        quickui.setIcon(self.dialog)
        self.wizardprogress = _WizardProgress()
        self.wizardprogress.show()
        self.wizardprogress.set_text(self._get_text())

        self.dialog.resize(400,200)
        self._setupButtons()
        self._setupSignals()
        self._initActionArea()
        self._setupActionArea()
        self._setupContents()
        self.pages[self.current].widget.show()

    def _setupContents(self):
        self.dialog.vbox.pack_start(self.pages[self.current].widget, False, False, 0)
        self.dialog.vbox.pack_end(self.wizardprogress, False, False, 0)

    def _setupButtons(self):
        self.back = gtk.Button(stock=gtk.STOCK_GO_BACK)
        self.next = gtk.Button(stock=gtk.STOCK_GO_FORWARD)
        self.cancel = gtk.Button(stock=gtk.STOCK_CANCEL)
        self.finish = gtk.Button("Finish")
        self.buttons = [self.back, self.next, self.cancel, self.finish]

    def _setupActionArea(self):
        def _hide(b):
            try:
                b.hide()
            except:
                pass
        [_hide(b) for b in self.buttons]
        [b.set_sensitive(True) for b in self.buttons]

        self.cancel.show()
        self.back.show()

        if self._isFirst():#first
            self.back.set_sensitive(False)
            self.next.show()
        elif self._isLast():
            self.finish.show()
        else:#other
            self.next.show()
            
    def _setupSignals(self):
        """
        setup Signals for buttons cancel, back, next and finish
        """
        self.back.connect("clicked",self._onBack)
        self.next.connect("clicked",self._onNext)
        self.cancel.connect("clicked", self._onCancel)
        self.finish.connect("clicked", self._onFinish)

    def _initActionArea(self):
        self.dialog.action_area.pack_start(self.cancel, True, False, 5)
        self.dialog.action_area.pack_start(self.back, True, False, 0)
        self.dialog.action_area.pack_start(self.next, True, False, 0)
        self.dialog.action_area.pack_start(self.finish, True, False, 0)

    def _onBack(self, button):
        """
        function to be executed when "back" button is pressed
        """
        self.dialog.vbox.remove(self.pages[self.current].widget)
        try:
            self.current = self.history.pop()
            print "self.current", self.current
        except IndexError, e:
            pass
        self._showPage(self.current)
        self._setupActionArea()

    def _getEnv(self):
        l = {}
        l['state'] = self.state
        l['output'] = self.output
        return l

    def _evalBoolean(self, script, _globals, _locals):
        try:
            return eval(script, _globals, _locals)
        except KeyError, e:
            print e
            return False
        except Exception, e:
            print e
            return False

    def _getNextLocation(self):
        print self.current,"_getNextLocation"
        branches = self.floworder[self.current]
        l = self._getEnv()
        for b in branches:
            if self._evalBoolean(b[1], l, l):
                return b[0]
        return None

    def _isLast(self):
        return self.current == self.pageids[-1]

    def _isFirst(self):
        return not self.history
        
    def _execpre(self, location):
        """
        execute preprocess of given page. location is position of page.
        """
        try:
            self.pages[location].preprocess(self.state)
            return True
        except Exception, e:
            quickui.error(parent=self.dialog, message=e.message)
            return False

    def _execpost(self, location):
        """
        execute preprocess of given page. location is position of page.
        """
        try:
            self.pages[location].postprocess(self.state, self.output)
            return True
        except Exception, e:
            quickui.error(parent=self.dialog, message=e.message)
            return False

    def _showPage(self, location):
        """
        show page, update dialog title etc.
        """
        p = self.pages[location]
        self.dialog.vbox.pack_start(p.widget, False, False, 0)
        p.widget.show()
        self.wizardprogress.set_fraction(self._get_fraction())
        self.wizardprogress.set_text(self._get_text())
        self.dialog.set_title(self._get_title())

    def _onNext(self, button):
        """
        Method to be executed when next button is pressed.
        """
        if self._execpost(self.current):
            c = self._getNextLocation()
            if c == "*" or None:
                self._onFinish(button)
                return
            if self._execpre(c):
                print "prev = ", self.current
                self.dialog.vbox.remove(self.pages[self.current].widget)
                self.history.append(self.current)
                self.current = c
                print "current = ", c
                self._showPage(self.current)
                #self.pages[self.current].widget.show()
            self._setupActionArea()

    def _cleanup(self):
        map(lambda x: x.widget.quickcleanup(), self.pages.values())
        
    def _onFinish(self, button):
        """
        Method to be executed when finish button is pressed.
        """
        if self._execpost(self.current):
            self._cleanup()
            self.dialog.destroy()

    def _onCancel(self, button):
        """
        Method to be executed when cancel button is pressed
        """
        response = quickui.question(parent=self.dialog, message="Wizard will be canceled, are you sure?")
        if response==gtk.RESPONSE_YES:
            self.output = None
            self._cleanup()
            self.dialog.destroy()

    def runWizard(self):
        response = self.dialog.run()
        return self.output

class Wizpage:
    """
    This is default class for wizard page. Wizard can be run from list of such 
    pages. To create a wizard page one should extend this class and implement
    only required methods, i.e. preprocess and postprocess.

    Other fields in Wizpage

    pageid= id of page
    title= title of page
    description= description of page. Will be shown as description on top.
    pagecontents= UI elements of this page

    """

    def __init__(self, pageid="pageid", title="Title", description="Description for this page"):
        self.pageid = pageid
        self.title = title
        self.description = description
        self.pagecontents = self._getWidget()
        self.compose()

    def _getWidget(self):
        """
        Override this method to create a default widget for this page
        """
        c = gtk.Label("Please place widgets of your choice here!")
        c1 = quickui.createWidget(type="Custom", quickid = "dummy", component=c)
        return quickui.createWidget(type="Group", quickid=self.pageid, components=[c1])
    

    def _getDescription(self):
        """
        A default method to create description label on top of page.
        """
        l = gtk.Label(self.description)
        l.set_justify(gtk.JUSTIFY_LEFT)
        l.set_line_wrap(True)
        l.show()
        hb = gtk.HBox()
        hb.pack_start(l, False, False, 10)
        w = quickui.createWidget(type="Custom", quickid="dummy", component = hb)
        w.modify_bg(gtk.STATE_NORMAL,gtk.gdk.color_parse("white"))
        return w

    def compose(self):
        """
        Creates a composite widget from this page's widget with description.
        call this method when ever you change self.pagecontents dynamically.
        """
        self.descriptionlabel = self._getDescription()
        self.widget = quickui.createWidget(type="Group", quickid=self.pageid, components = [self.descriptionlabel, self.pagecontents], addSeperator=True)
        print "composed", self.pageid

    def preprocess(self, state):
        """
        This method will be called before the page is shown.
        This is ideal place for creating dynamic contents of page
        depending on state.
        """
        print "Probably you did not define preprocess method in your wizpage!"

    def postprocess(self, state, output):
        """
        This method will be called when next or finish is pressed.
        This populated outputs from inputs collected on this page.
        """
        if self.pageid in self.widget.getValue():
            output[self.pageid] = self.widget.getValue()[self.pageid]
        else:
            output[self.pageid] = self.widget.getValue()


def runWizard(module, inputs={}, parent=None):
    w = _Wizard(module.title, module.getPages(), module.floworder, inputs, parent=parent)
    return w.runWizard()

if __name__=="__main__":
    import samplewizard
    const.home = os.getcwd()
    print runWizard(samplewizard)
