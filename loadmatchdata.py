import dearpygui.dearpygui as dpg
import numpy as np
import csv
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import csv
import pandas as pd
def load_match_data():
    filename = filedialog.askopenfilename()
    colNames = ["Timestamp", "Name", "Value"]
    dataFrame = pd.read_csv(filename, names=colNames)
    dataFrame = dataFrame[1:]

    red_or_blue = dataFrame.query("Name == 'NT:/FMSInfo/IsRedAlliance'")["Value"].item()
    match_number = dataFrame.query("Name == 'NT:/FMSInfo/MatchNumber'")["Value"].item()
    station_number = dataFrame.query("Name == 'NT:/FMSInfo/StationNumber'")["Value"].item()
    print('Alliance Color = ', red_or_blue, 'Match Number = ', match_number, 'Driver Station ', station_number)
