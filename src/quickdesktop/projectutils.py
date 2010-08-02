from quickdesktop import common 
from quickdesktop import events
import unittest

PROJECT_OPENED = "PROJECT_OPENED"
PROJECT_CLOSED = "PROJECT_CLOSED"
PROJECT_ACTIVATED = "PROJECT_ACTIVATED"

class ProjectManager(common.Singleton):
    """
    Project manager manages project in the desktop application.
    It manages list of open projects in the system. It allows multiple projects
    to be open at a time.

    It has concept of active project. It also handles following events.

    PROJECT_OPENED : fired on opening a project. when you open a project 
    it is also active by default.

    PROJECT_CLOSED : fired on closing the project.

    PROJECT_ACTIVATED : fired when some project is activated.

    """

    def __init__(self):
        if 'projects' not in vars(self):
            self.projects = []
            self.activeproject = None

    def addProject(self, p):
        self.projects.append(p)
        self.activeproject = p
        eventdata = {'type':PROJECT_OPENED}
        eventdata['origin'] = self
        eventdata['project'] = p
        events.EventMulticaster().dispatchEvent(PROJECT_OPENED,eventdata)

    def removeProject(self, p):
        if p in self.projects:
            self.projects.remove(p)
            eventdata = {'type':PROJECT_CLOSED}
            eventdata['origin'] = self
            eventdata['project'] = p
            events.EventMulticaster().dispatchEvent(PROJECT_CLOSED, eventdata)
        if p == self.activeproject and self.projects:
            self.setActiveProject(self.projects[0])

    def setActiveProject(self, p):
        if p in self.projects and p!= self.activeproject :
            self.activeproject = p
            eventdata = {'type':PROJECT_ACTIVATED}
            eventdata['origin'] = self
            eventdata['project'] = p
            events.EventMulticaster().dispatchEvent(PROJECT_ACTIVATED, eventdata)
            

def getActiveProject():
    return ProjectManager().activeproject

def addProject(project):
    ProjectManager().addProject(project)

def removeProject(project):
    ProjectManager().removeProject(project)

def setActiveProject(project):
    ProjectManager().setActiveProject(project)



