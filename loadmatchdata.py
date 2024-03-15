import dearpygui.dearpygui as dpg
import numpy as np
import csv
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import csv
import pandas as pd

def load_match_data_from_file():
    filename = filedialog.askopenfilename()
    colNames = ["Timestamp", "Name", "Value"]
    dataFrame = pd.read_csv(filename, names=colNames)
    dataFrame = dataFrame[1:]
    return(dataFrame)

def get_initial_match_data(dataFrame):  
    red_or_blue = dataFrame.query("Name == 'NT:/FMSInfo/IsRedAlliance'")["Value"].item()
    match_number = dataFrame.query("Name == 'NT:/FMSInfo/MatchNumber'")["Value"].item()
    station_number = dataFrame.query("Name == 'NT:/FMSInfo/StationNumber'")["Value"].item()
    return(red_or_blue, match_number, station_number)
    
def get_match_data():
    dataFrame = load_match_data_from_file()
    initial_data = get_initial_match_data(dataFrame)
    pose_data = get_pose_data(dataFrame)
    return(initial_data, pose_data)

def get_pose_data(dataFrame):
    pose_data = dataFrame.query("Name == 'odometry'")
    # formatted_pose_data = pd.DataFrame(columns=['X', 'Y', 'Rot'])

    # for i in len(pose_data):
    #     current_pose = pose_data.iloc[[i]]
    #     split_data = current_pose.split(": ", 3)
    #     print(split_data)
        
    #     formatted_pose_data.append()
    return(pose_data)