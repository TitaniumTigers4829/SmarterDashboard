import dearpygui.dearpygui as dpg
import numpy as np
import csv
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import csv
import pandas as pd
def load_match_data(event=None):
    filename = filedialog.askopenfilename()

    dataframe = pd.read_csv(filename)
    red_or_blue = dataframe.query("NT:/FMSInfo/IsRedAlliance")
    print(red_or_blue)