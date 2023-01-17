from time import sleep
from score_tracker import *

from networktables import NetworkTablesInstance

# Constants for the names of network table entries
HAS_UPPERTERMINAL1_SCORED = ""
HAS_UPPERTERMINAL2_SCORED = ""
HAS_UPPERTERMINAL3_SCORED = ""
HAS_UPPERTERMINAL4_SCORED = ""
HAS_UPPERTERMINAL5_SCORED = ""
HAS_UPPERTERMINAL6_SCORED = ""
HAS_UPPERTERMINAL7_SCORED = ""
HAS_UPPERTERMINAL8_SCORED = ""
HAS_UPPERTERMINAL9_SCORED = ""
HAS_MIDDLETERMINAL1_SCORED = ""
HAS_MIDDLETERMINAL2_SCORED = ""
HAS_MIDDLETERMINAL3_SCORED = ""
HAS_MIDDLETERMINAL4_SCORED = ""
HAS_MIDDLETERMINAL5_SCORED = ""
HAS_MIDDLETERMINAL6_SCORED = ""
HAS_MIDDLETERMINAL7_SCORED = ""
HAS_MIDDLETERMINAL8_SCORED = ""
HAS_MIDDLETERMINAL9_SCORED = ""
HAS_LOWERTERMINAL1_SCORED = ""
HAS_LOWERTERMINAL2_SCORED = ""
HAS_LOWERTERMINAL3_SCORED = ""
HAS_LOWERTERMINAL4_SCORED = ""
HAS_LOWERTERMINAL5_SCORED = ""
HAS_LOWERTERMINAL6_SCORED = ""
HAS_LOWERTERMINAL7_SCORED = ""
HAS_LOWERTERMINAL8_SCORED = ""
HAS_LOWERTERMINAL9_SCORED = ""



def scoreUpdater(nt: NetworkTable):
    """
    Handles receiving the climb zeroes from the robot.
    :param nt: The network table created from the .getTable method.
    :return:
    """
    ntinst = NetworkTablesInstance.getDefault()
    ntinst.startClientTeam(4829)
    ntinst.startDSClient()
    
    values_received = False
    while not values_received:
        # Gets the climb zeroes from the network table

        lowerTerminal1 = nt.getBoolean(HAS_LOWERTERMINAL1_SCORED, False)
        lowerTerminal2 = nt.getBoolean(HAS_LOWERTERMINAL2_SCORED, False)
        lowerTerminal3 = nt.getBoolean(HAS_LOWERTERMINAL3_SCORED, False)
        lowerTerminal4 = nt.getBoolean(HAS_LOWERTERMINAL4_SCORED, False)
        lowerTerminal5 = nt.getBoolean(HAS_LOWERTERMINAL5_SCORED, False)
        lowerTerminal6 = nt.getBoolean(HAS_LOWERTERMINAL6_SCORED, False)
        lowerTerminal7 = nt.getBoolean(HAS_LOWERTERMINAL7_SCORED, False)
        lowerTerminal8 = nt.getBoolean(HAS_LOWERTERMINAL8_SCORED, False)
        lowerTerminal9 = nt.getBoolean(HAS_LOWERTERMINAL9_SCORED, False)
        middleTerminal1 = nt.getBoolean(HAS_MIDDLETERMINAL1_SCORED, False)
        middleTerminal2 = nt.getBoolean(HAS_MIDDLETERMINAL2_SCORED, False)
        middleTerminal3 = nt.getBoolean(HAS_MIDDLETERMINAL3_SCORED, False)
        middleTerminal4 = nt.getBoolean(HAS_MIDDLETERMINAL4_SCORED, False)
        middleTerminal5 = nt.getBoolean(HAS_MIDDLETERMINAL5_SCORED, False)
        middleTerminal6 = nt.getBoolean(HAS_MIDDLETERMINAL6_SCORED, False)
        middleTerminal7 = nt.getBoolean(HAS_MIDDLETERMINAL7_SCORED, False)
        middleTerminal8 = nt.getBoolean(HAS_MIDDLETERMINAL8_SCORED, False)
        middleTerminal9 = nt.getBoolean(HAS_MIDDLETERMINAL9_SCORED, False)
        upperTerminal1 = nt.getBoolean(HAS_UPPERTERMINAL1_SCORED, False)
        upperTerminal2 = nt.getBoolean(HAS_UPPERTERMINAL2_SCORED, False)
        upperTerminal3 = nt.getBoolean(HAS_UPPERTERMINAL3_SCORED, False)
        upperTerminal4 = nt.getBoolean(HAS_UPPERTERMINAL4_SCORED, False)
        upperTerminal5 = nt.getBoolean(HAS_UPPERTERMINAL5_SCORED, False)
        upperTerminal6 = nt.getBoolean(HAS_UPPERTERMINAL6_SCORED, False)
        upperTerminal7 = nt.getBoolean(HAS_UPPERTERMINAL7_SCORED, False)
        upperTerminal8 = nt.getBoolean(HAS_UPPERTERMINAL8_SCORED, False)
        upperTerminal9 = nt.getBoolean(HAS_UPPERTERMINAL9_SCORED, False)

        for i in range(1,10):
            if 'upperTerminal' + str(i) != False:
                ScoreTracker.peiceScored('upperTerminal' + str(i))

        for i in range(1,10):
            if 'middleTerminal' + str(i) != False:
                ScoreTracker.peiceScored('middleTerminal' + str(i))

        for i in range(1,10):
            if 'lowerTerminal' + str(i) != False:
                ScoreTracker.peiceScored('lowerTerminal' + str(i))