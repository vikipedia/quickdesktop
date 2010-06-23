from quickdesktop import wizard
from quickdesktop import quickui


title = "Sample wizard"

#This module is one sample wizard which demonstrates how to 
#create wizard.

class Samplepage1(wizard.Wizpage):
    """
    This is a class of for page Samplepage1.
    """
    
    def __init__(self, pageid="Samplepage1", title="Sample page1",
                 description="""
This page displays sample wizard page. Select the path of wizard. This description should line wrap.
"""
                 ):
        wizard.Wizpage.__init__(self, pageid= pageid, title=title, description=description)

    
    def _getWidget(self):
        c1 = quickui.createWidget(quickid="name",type="String",value="Vikrant", description="Name")
        c2 = quickui.createWidget(quickid="company",type="String",value="Freelance",description="Company") 
        c3 = quickui.createWidget(quickid="whichway",type="Enum",description="Which way?", value="Left", options = ["Left", "Right"])
        return quickui.createWidget(quickid=self.pageid,type="Group", components=[c1,c2,c3])
        
class Left(wizard.Wizpage):
    """
    This is a class for page Left.
    """
    def __init__(self, pageid="Left", title="Left",
                 description="""
This page displays Left page!
"""
                 ):
        wizard.Wizpage.__init__(self, pageid=pageid, title=title, description=description)
    
    def _getWidget(self):
        c1 = quickui.createWidget(quickid="Way",type="String",value="Left", description="Name")
        return quickui.createWidget(quickid=self.pageid, type="Group", components=[c1])

class Right(wizard.Wizpage):
    """
    This class represents page Right
    """
    def __init__(self, pageid="Right", title="Right",
                 description="""
This page displays Right page!
"""
                 ):
        wizard.Wizpage.__init__(self, pageid=pageid, title=title, description=description)
    
    def _getWidget(self):
        c1 = quickui.createWidget(quickid="Way",type="String",value="Right", description="Name")
        return quickui.createWidget(quickid=self.pageid, type="Group", components=[c1])



class Last(wizard.Wizpage):
    """
    This is Last page of the wizard.
    """
    def __init__(self, pageid="last", title="Last",
                 description="""
This page displays Last page!
It ends here.
"""
                 ):
        wizard.Wizpage.__init__(self, pageid=pageid, title=title, description=description)
    
    def _getWidget(self):
        from quickui import createWidget
        s1 = createWidget(type="String",quickid="bx",value="testxxx", maxlength=10)
        s2 = createWidget(type="Integer",quickid="by",value=5, maxvalue=10)
        s5 = createWidget(type="Enum",quickid="bz",options={'a':"Asdsfdfdsfdsfdsfdsfds",'b':"B",'c':"C"}, value="c")
        s5.setValue("b")
        s6 = createWidget(type="Boolean",quickid="bp",description="Select this", value=True)
        s7 = createWidget(type="QFileChooser",quickid="file",description="Choose file", value="/home/vikrant/examples.desktop")
        s6.connect("toggled",lambda w1,w2: w2.set_sensitive(w1.getValue()), s7)
        w= createWidget(type="Group",quickid=self.pageid,components=[s1,s2,s5,s6,s7])
        return createWidget(type="ScrolledWidget", widget = w)


#pagelist is a list which includes all the pages that you would like to 
#see in the wizard
def getPages():
    pagelist = [Samplepage1(), Left(), Right(), Last()]
    return pagelist

#floworder is dictinary which tells flow logic of the wizard.
floworder = {
    "*":[("Samplepage1", "True")], #start condition
    "Samplepage1":[
        ("Left","output['Samplepage1']['whichway']=='Left'"),
        ("Right", "output['Samplepage1']['whichway']=='Right'")],
    "Left":[("last","True")],
    "Right":[("last","True")],
    "last":[("*","True")]}#end condition
