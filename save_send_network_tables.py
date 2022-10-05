from time import sleep

from _pynetworktables import *

# Constants for the names of network table entries
RECEIVE_LEFT_NAME = "leftClimbHookHeight"
RECEIVE_RIGHT_NAME = "rightClimbHookHeight"
SEND_LEFT_NAME = "leftClimbHookZero"
SEND_RIGHT_NAME = "rightClimbHookZero"
SEND_CONFIRMATION_NAME = "leftZeroReceivedSuccessfully"


def receive_climb_values(nt: NetworkTable):
    """
    Handles receiving the climb zeroes from the robot.
    :param nt: The network table created from the .getTable method.
    :return:
    """
    values_received = False
    while not values_received:
        # Gets the climb zeroes from the network table
        left_climb_zero = nt.getNumber(RECEIVE_LEFT_NAME, -1)
        right_climb_zero = nt.getNumber(RECEIVE_RIGHT_NAME, -1)
        sleep(3)
        if left_climb_zero != -1 and right_climb_zero != -1:
            # Saves the climb zeroes in a text file
            values_received = True


def send_climb_values(nt: NetworkTable):
    """
    Handles sending the saved climb zeroes to the robot.
    :param nt: The network table created from the .getTable method.
    :return:
    """
    # Gets the saved zeroes from the text file
    values_sent = False
    while not values_sent:
        # Puts the saved zeroes in the network table
        nt.putNumber(SEND_LEFT_NAME, float(0))
        nt.putNumber(SEND_RIGHT_NAME, float(0))
        sleep(3)
        values_sent = verify_values_were_sent(nt)


def verify_values_were_sent(nt: NetworkTable) -> bool:
    """
    This function uses another network table entry to verify that the robot received the sent zeroes.
    :param nt: The network table created from the .getTable method.
    :return: True if the robot successfully received the zeroes, False if not.
    """
    # Gets the climb zeroes from the network table
    send_confirmation = nt.getBoolean(SEND_CONFIRMATION_NAME, False)
    sleep(3)
    return send_confirmation
