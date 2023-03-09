from networktables import NetworkTablesInstance
from networktables.util import ChooserControl
import time

ntinst = NetworkTablesInstance.getDefault()
ntinst.startClientTeam(4829)
ntinst.startDSClient()
sd_table = ntinst.getTable("SmartDashboard")


class NetworkTableValue:
    def __init__(self, name, on_change=None):
        self.name = name,
        self.on_change = on_change
        if on_change is not None:
            sd_table.addEntryListener(on_change, True, name)


class Chooser:
    def __init__(self, name, on_choices=None, on_selected=None):
        self.name = name
        if on_choices is not None and on_selected is not None:
            self.cc = ChooserControl("SmartDashboard/" + name, on_choices, on_selected, inst=ntinst)

    def getValues(self):
        return self.cc.getChoices()

    def getSelected(self):
        return self.cc.getSelected()

    def setSelected(self, choice):
        self.cc.setSelected(choice)


def getAllValues():
    return ntinst._api.storage.m_entries