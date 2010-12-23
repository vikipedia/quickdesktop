from quickdesktop.common import Singleton
from quickdesktop import common
import unittest, random


def addEventListener(eventType, listener, code, data):
    """
    creates a function required by EventMulticaster().addListener()
    and adds the required listener.
    code has to written with assumption that it is body of function
    with two arguments with names listener and eventData
    """
    funcname = getFunctionName(eventType)
    firstline = "def %s(listenerObject, eventData):"%funcname
    CODE = "\n".join([firstline] + ["\t"+i for i in code.strip().split("\n")])
    g = dict(data)
    eval(compile(CODE, "error.log", "exec"), g, g)
    EventMulticaster().addListener(eventType, listener, g[funcname])

def getFunctionName(eventType):
    """
    returns name of callback function for given eventType
    """
    return "on_" + eventType

class EventMulticaster(Singleton):
    """
    EventMulticaster is common class whcih takes care of all 
    events in the system. It saves list of listeners for 
    all the events. When ever event ocuurs this class will 
    call on_EVENT_TYPE method on listners.
    """

    def __init__(self):
        if "listeners" not in vars(self):
            self.listeners = {}

    def dispatchEvent(self, eventType, eventdata):
        """
        calls callback on all the listeners of event type "eventType"
        """

        if eventType in self.listeners:
            l = self.listeners[eventType]
            for listener in l:
                eval("listener.%s(listener, eventdata)"%getFunctionName(eventType), globals(), locals())


    def addListener(self, eventType, listener, func):
        """
        Adds listener to given eventType
        """
        S = "listener.%s = func"%func.__name__
        eval(compile(S,"error.log","exec"), globals(), locals())

        if eventType in self.listeners: 
            self.listeners[eventType].append(listener)
        else:
            self.listeners[eventType] = [listener]

    def removeListener(self, eventType, listener):
        """
        removes the listener from given event
        """
        if eventType in self.listeners:
            self.listeners[eventType].remove(listener)

    def removeAllListeners(self, eventType):
        """
        removes all listeners of given eventType.
        Use this carefully! You should know what you are doing before 
        using this function.
        """
        if eventType in self.listeners:
            del self.listeners[eventType]
        

class Test_SOME_EVENT_Listener:
    def __init__(self):
        self.flag = True
        self.data = range(10000)
        
class TestEventMultiCaster(unittest.TestCase):
    
    def setUp(self):
        self.multicaster = EventMulticaster()
        
    def testAddListener(self):
        l = Test_SOME_EVENT_Listener()
        addEventListener("SOME_EVENT", l, "listenerObject.flag = not listenerObject.flag", {})

        flag = l.flag
        self.multicaster.dispatchEvent("SOME_EVENT", {"type":"SOME_EVENT", "origin":self})
        self.assertEqual(flag, not l.flag)
        self.multicaster.removeListener("SOME_EVENT", l)

    def testRemoveListenr(self):
        CODE ="""
	listenerObject.flag = not listenerObject.flag"""
        l = Test_SOME_EVENT_Listener()

        addEventListener("SOME_EVENT", l, CODE, {})
        self.multicaster.dispatchEvent("SOME_EVENT", {"type":"SOME_EVENT", "origin":self})
        flag = l.flag
        self.multicaster.removeListener("SOME_EVENT", l)
        self.multicaster.dispatchEvent("SOME_EVENT", {"type":"SOME_EVENT", "origin":self})
        self.assertEqual(flag, l.flag)        

if __name__=="__main__":
    unittest.main()
        
