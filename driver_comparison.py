''' UI LIBRARIES'''
# PyQt5
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStyledItemDelegate
from PyQt5.QtGui import *
from PyQt5.QtCore import * 
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
import PyQt5.uic as uic 

# FastF1 API
import fastf1 as ff1

# Plotting Libraries
import pyqtgraph as pg
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as  FigureCanvas
from matplotlib.collections import LineCollection
import geojson

# Data Analysis Libraries
import numpy as np
import pandas as pd
import re
from scipy import interpolate 

class UI_driver(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        uic.loadUi('driver_comparison_page.ui', self)

        # Stylizing the QComboBoxes with the applied QSS in .ui file
        self.driver1.setItemDelegate(QStyledItemDelegate(self.driver1))
        self.driver2.setItemDelegate(QStyledItemDelegate(self.driver2))
        self.driver3.setItemDelegate(QStyledItemDelegate(self.driver3))
        self.lap_sel1.setItemDelegate(QStyledItemDelegate(self.lap_sel1))
        self.lap_sel2.setItemDelegate(QStyledItemDelegate(self.lap_sel2))
        self.lap_sel3.setItemDelegate(QStyledItemDelegate(self.lap_sel3))
            
        '''
        INITIALIZING ALL REQUIRED MATRICES:
        Includes:
            Lap selection matrixes, 
            Lap-time display matrixes, 
            Driver Color matrices
        '''
        self.driver_colors_disp = [self.driv_color1, self.driv_color2, self.driv_color3]
        self.driver_laptimes_disp = [self.driver1_laptime, self.driver2_laptime, self.driver3_laptime]
        self.driver_sector1_disp = [self.driver1_sector1, self.driver2_sector1, self.driver3_sector1]
        self.driver_sector2_disp = [self.driver1_sector2, self.driver2_sector2, self.driver3_sector2]
        self.driver_sector3_disp = [self.driver1_sector3, self.driver2_sector3, self.driver3_sector3]

        self.set_plot_displays()

        # Loading laps for each selected driver
        self.driver1.currentIndexChanged.connect(lambda: self.laps_select(0))
        self.driver2.currentIndexChanged.connect(lambda: self.laps_select(1))
        self.driver3.currentIndexChanged.connect(lambda: self.laps_select(2))

        # Clearing Driver Data
        self.clear_signal = False
        self.clear1.clicked.connect(lambda: self.clear_driver(0))
        self.clear2.clicked.connect(lambda: self.clear_driver(1))
        self.clear3.clicked.connect(lambda: self.clear_driver(2))

        # Setting the fastest lap of selected drivers
        self.fast1.clicked.connect(lambda: self.set_fastest_lap(0))
        self.fast2.clicked.connect(lambda: self.set_fastest_lap(1))
        self.fast3.clicked.connect(lambda: self.set_fastest_lap(2))   
        
        # Initializing Matrices
        self.laps = ['','','']
        self.speed_tel1 = ['','','']
        self.brake_tel1 = ['','','']
        self.rpm_tel1 = ['','','']
        self.throttle_tel1 = ['','','']
        self.ngear_tel1 = ['','','']
        self.drs_tel1 = ['','','']

        self.speed_tel2 = ['','','']
        self.brake_tel2 = ['','','']
        self.rpm_tel2 = ['','','']
        self.throttle_tel2 = ['','','']
        self.ngear_tel2 = ['','','']
        self.drs_tel2 = ['','','']

        self.driver_laptimes = ['','','']
        self.driver_laps = ['','','']
        self.driver_sector1_times = ['','','']
        self.driver_sector2_times = ['','','']
        self.driver_sector3_times = ['','','']
        self.tyre_compounds = ['','','']

        # Loading Data
        self.lap_sel1.currentIndexChanged.connect(lambda: self.load_compare_data(0))
        self.lap_sel2.currentIndexChanged.connect(lambda: self.load_compare_data(1))
        self.lap_sel3.currentIndexChanged.connect(lambda: self.load_compare_data(2))

    # Setting the telemetry plot displays
    def set_plot_displays(self):
        self.speed1p_legend = self.speed1p.addLegend()
        self.speed1p.setLabel('left', 'Speed', units ='km/h')
        self.speed1p.setLabel('bottom', 'Distance', units ='km') 

        self.speed2p_legend = self.speed2p.addLegend()
        self.speed2p.setLabel('left', 'Speed', units ='km/h')
        self.speed2p.setLabel('bottom', 'Distance', units ='km') 
        
        self.rpm1p_legend = self.rpm1p.addLegend()
        self.rpm1p.setLabel('left', 'RPM', units ='x1000')
        self.rpm1p.setLabel('bottom', 'Distance', units ='km') 
        
        self.rpm2p_legend = self.rpm2p.addLegend()
        self.rpm2p.setLabel('left', 'RPM', units ='x1000')
        self.rpm2p.setLabel('bottom', 'Distance', units ='km') 
        
        self.throttle1p_legend = self.throttle1p.addLegend()
        self.throttle1p.setLabel('left', 'Throttle')
        self.throttle1p.setLabel('bottom', 'Distance', units ='km') 
        
        self.throttle2p_legend = self.throttle2p.addLegend()
        self.throttle2p.setLabel('left', 'Throttle')
        self.throttle2p.setLabel('bottom', 'Distance', units ='km') 
        
        self.brake1p_legend = self.brake1p.addLegend()
        self.brake1p.setLabel('left', 'Brake')
        self.brake1p.setLabel('bottom', 'Distance', units ='km') 
        
        self.brake2p_legend = self.brake2p.addLegend()
        self.brake2p.setLabel('left', 'Brake')
        self.brake2p.setLabel('bottom', 'Distance', units ='km') 
        
        self.ngear1p_legend = self.ngear1p.addLegend()
        self.ngear1p.setLabel('left', 'nGear')
        self.ngear1p.setLabel('bottom', 'Distance', units ='km') 
        
        self.ngear2p_legend = self.ngear2p.addLegend()
        self.ngear2p.setLabel('left', 'nGear')
        self.ngear2p.setLabel('bottom', 'Distance', units ='km')

        self.drs1p_legend = self.drs1p.addLegend()
        self.drs1p.setLabel('left', 'DRS')
        self.drs1p.setLabel('bottom', 'Distance', units ='km')

        self.drs2p_legend = self.drs2p.addLegend()
        self.drs2p.setLabel('left', 'DRS')
        self.drs2p.setLabel('bottom', 'Distance', units ='km')

        self.track_dom_p.getPlotItem().hideAxis('bottom')
        self.track_dom_p.getPlotItem().hideAxis('left')
        self.track_dom_p.setAspectLocked()
        self.track_dom_p.setMouseEnabled(x=True, y=False)
        self.track_dom_p.setBackground('#171718')
        self.track_dom_p.setAutoPan()

    def disable_drivers(self, initial_load: bool):
        self.initial_load = initial_load

        self.driver1.clear()
        self.driver2.clear()
        self.driver3.clear()
        self.lap_sel1.clear()
        self.lap_sel2.clear()
        self.lap_sel3.clear()
        self.speed1p.clear()
        self.speed2p.clear()
        self.rpm1p.clear()
        self.rpm2p.clear()
        self.throttle1p.clear()
        self.throttle2p.clear()
        self.brake1p.clear()
        self.brake2p.clear()
        self.ngear1p.clear()
        self.ngear2p.clear()
        self.drs1p.clear()
        self.drs2p.clear()
        self.deltap.clear()
        self.track_dom_p.clear()

        self.speed_tel1 = ['','','']
        self.brake_tel1 = ['','','']
        self.rpm_tel1 = ['','','']
        self.throttle_tel1 = ['','','']
        self.ngear_tel1 = ['','','']
        self.drs_tel1 = ['','','']

        self.speed_tel2 = ['','','']
        self.brake_tel2 = ['','','']
        self.rpm_tel2 = ['','','']
        self.throttle_tel2 = ['','','']
        self.ngear_tel2 = ['','','']
        self.drs_tel2 = ['','','']

        self.driver_laptimes = ['','','']
        self.driver_laps = ['','','']
        self.driver_sector1_times = ['','','']
        self.driver_sector2_times = ['','','']
        self.driver_sector3_times = ['','','']
        self.tyre_compounds = ['','','']

        self.driver1_compound.setIcon(QIcon())
        self.driver2_compound.setIcon(QIcon())
        self.driver3_compound.setIcon(QIcon())

        for id in range(3):
            self.driver_colors_disp[id].setStyleSheet('background-color: #28282a')
            self.driver_laptimes_disp[id].clear()
            self.driver_sector1_disp[id].clear()
            self.driver_sector2_disp[id].clear()
            self.driver_sector3_disp[id].clear()
        
        self.driver1.setEnabled(False)
        self.driver2.setEnabled(False)
        self.driver3.setEnabled(False)
        self.clear1.setEnabled(False)
        self.clear2.setEnabled(False)
        self.clear3.setEnabled(False)

        self.initial_load = False
    
    def enable_drivers(self):
        self.driver1.setEnabled(True)
        self.driver2.setEnabled(True)
        self.driver3.setEnabled(True)
        self.clear1.setEnabled(True)
        self.clear2.setEnabled(True)
        self.clear3.setEnabled(True)
    
    def receive_parameters(self, current_session, circuit_info, initial_load):
        self.current_session = current_session
        self.circuit_info = circuit_info
        self.initial_load = initial_load
        self.drivers_select()
    
    # Adding Drivers from the selected Session to combo box
    def drivers_select(self):
        self.enable_drivers()
        drivers = getattr(self.current_session, 'drivers')    

        # Adding Drivers list to Combo Box
        for driver in drivers:
            name = self.current_session.get_driver(driver)
            self.driver1.addItem(name['DriverNumber'].zfill(2) + ":  " + name['FullName'])
            self.driver2.addItem(name['DriverNumber'].zfill(2) + ":  " + name['FullName']) 
            self.driver3.addItem(name['DriverNumber'].zfill(2) + ":  " + name['FullName'])

    # Converting driver strings to only driver numbers
    def get_driver_no(self):
        self.drivers = [self.driver1.currentText(), self.driver2.currentText(), self.driver3.currentText()]
        for i, driver in enumerate(self.drivers):
            if self.drivers[i] == '':
                self.drivers[i] = '0'

            else:
                temp = re.findall(r'\b\d+\b', self.drivers[i])
                self.drivers[i] = temp[0].lstrip("0") 
    
    '''
    Updating the headshots for the selected driver
        id: index for which driver is being updated
    '''
    def update_headshot(self, id):   
        driver_headshot = QIcon('images/driver_headshots/' + str(self.current_session.date.year) + '/' + self.drivers[id] + '.webp')
        if id == 0:
            self.headshot1.setIcon(driver_headshot)
        elif id == 1:
            self.headshot2.setIcon(driver_headshot)
        elif id == 2:
            self.headshot3.setIcon(driver_headshot)

    '''
    Adding all the laps completed by the selected driver;
    [Adds only hot-laps for qualifying and sprint qualifying/shootout sessions]
        id: index for which driver's laps are being added
    '''
    def laps_select(self, id):
        # Generating the driver number array
        self.get_driver_no()

        if id == 0:
            if not (self.driver1.currentText() == ''):
                self.lap_sel1.setEnabled(True)
                self.fast1.setEnabled(True)
                self.update_headshot(0)
                self.lap_sel1.clear()

                if (getattr(self.current_session, 'name') == 'Qualifying' or 
                    getattr(self.current_session, 'name') == 'Sprint Qualifying' or 
                    getattr(self.current_session, 'name') == 'Sprint Shootout'):
                    for i in range(len(self.current_session.laps.pick_driver(self.drivers[id]).pick_wo_box())):
                        self.lap_sel1.addItem('Lap ' + str(i+1))
                else:
                    for i in range(len(self.current_session.laps.pick_driver(self.drivers[id]))):
                        self.lap_sel1.addItem('Lap ' + str(i+1))
            
            else:
                self.headshot1.setIcon(QIcon())
                self.lap_sel1.setCurrentIndex(-1)
                self.lap_sel1.setEnabled(False)
                self.fast1.setEnabled(False)

        if id == 1:
            if not (self.driver2.currentText() == ''):
                self.lap_sel2.setEnabled(True)
                self.fast2.setEnabled(True)
                self.update_headshot(1)
                self.lap_sel2.clear()

                if (getattr(self.current_session, 'name') == 'Qualifying' or 
                    getattr(self.current_session, 'name') == 'Sprint Qualifying' or 
                    getattr(self.current_session, 'name') == 'Sprint Shootout'):
                    for i in range(len(self.current_session.laps.pick_driver(self.drivers[id]).pick_wo_box())):
                        self.lap_sel2.addItem('Lap ' + str(i+1))
                else:
                    for i in range(len(self.current_session.laps.pick_driver(self.drivers[id]))):
                        self.lap_sel2.addItem('Lap ' + str(i+1))

            else:
                self.headshot2.setIcon(QIcon())
                self.lap_sel2.setCurrentIndex(-1)
                self.lap_sel2.setEnabled(False)
                self.fast2.setEnabled(False)

        if id == 2:
            if not (self.driver3.currentText() == ''):
                self.lap_sel3.setEnabled(True)
                self.fast3.setEnabled(True)
                self.update_headshot(2)
                self.lap_sel3.clear()

                if (getattr(self.current_session, 'name') == 'Qualifying' or 
                    getattr(self.current_session, 'name') == 'Sprint Qualifying' or 
                    getattr(self.current_session, 'name') == 'Sprint Shootout'):
                    for i in range(len(self.current_session.laps.pick_driver(self.drivers[id]).pick_wo_box())):
                        self.lap_sel3.addItem('Lap ' + str(i+1))

                else:
                    for i in range(len(self.current_session.laps.pick_driver(self.drivers[id]))):
                        self.lap_sel3.addItem('Lap ' + str(i+1))

            else:
                self.headshot3.setIcon(QIcon())
                self.lap_sel3.setCurrentIndex(-1)
                self.lap_sel3.setEnabled(False)
                self.fast3.setEnabled(False)
        
        self.laps = [self.lap_sel1.currentText(), self.lap_sel2.currentText(), self.lap_sel3.currentText()]
    
    '''
    Setting the selected lap as the fastest lap completed by the driver
    [Due to the way FastF1 functions, this only included non-deleted laps completed by the driver]
        id: index for which driver is being updated
    '''
    def set_fastest_lap(self, id):
        if id == 0:
            if (getattr(self.current_session, 'name') == 'Qualifying' or 
                getattr(self.current_session, 'name') == 'Sprint Qualifying' or 
                getattr(self.current_session, 'name') == 'Sprint Shootout'):
                fastest_lap = self.current_session.laps.pick_driver(self.drivers[id]).pick_wo_box().pick_fastest()
                fastest_lap = fastest_lap['LapNumber']

                # Finding the number of stints completed by the driver
                stint = self.current_session.laps.pick_driver(self.drivers[id]).pick_wo_box()
                stint.reset_index(inplace = True, drop = True)

                # Finding the sting in which the fastest lap was completed
                fast_index = stint.index[stint['LapNumber']==fastest_lap].tolist()

                # Setting the current index of the lap selection combobox to that of the fastest lap
                self.lap_sel1.setCurrentIndex(fast_index[0])

            else:
                fastest_lap = self.current_session.laps.pick_driver(self.drivers[id]).pick_fastest()

                # Setting the current index of the lap selection combobox to that of the fastest lap
                self.lap_sel1.setCurrentIndex(int(fastest_lap['LapNumber']) - 1)
        
        if id == 1:
            if (getattr(self.current_session, 'name') == 'Qualifying' or 
                getattr(self.current_session, 'name') == 'Sprint Qualifying' or 
                getattr(self.current_session, 'name') == 'Sprint Shootout'):
                fastest_lap = self.current_session.laps.pick_driver(self.drivers[id]).pick_wo_box().pick_fastest()
                fastest_lap = fastest_lap['LapNumber']

                # Finding the number of stints completed by the driver
                stint = self.current_session.laps.pick_driver(self.drivers[id]).pick_wo_box()
                stint.reset_index(inplace = True, drop = True)

                # Finding the sting in which the fastest lap was completed
                fast_index = stint.index[stint['LapNumber']==fastest_lap].tolist()

                # Setting the current index of the lap selection combobox to that of the fastest lap
                self.lap_sel2.setCurrentIndex(fast_index[0])

            else:
                fastest_lap = self.current_session.laps.pick_driver(self.drivers[id]).pick_fastest()

                # Setting the current index of the lap selection combobox to that of the fastest lap
                self.lap_sel2.setCurrentIndex(int(fastest_lap['LapNumber']) - 1)

        if id == 2:
            if (getattr(self.current_session, 'name') == 'Qualifying' or 
                getattr(self.current_session, 'name') == 'Sprint Qualifying' or 
                getattr(self.current_session, 'name') == 'Sprint Shootout'):
                fastest_lap = self.current_session.laps.pick_driver(self.drivers[id]).pick_wo_box().pick_fastest()
                fastest_lap = fastest_lap['LapNumber']

                # Finding the number of stints completed by the driver
                stint = self.current_session.laps.pick_driver(self.drivers[id]).pick_wo_box()
                stint.reset_index(inplace = True, drop = True)

                # Finding the sting in which the fastest lap was completed
                fast_index = stint.index[stint['LapNumber']==fastest_lap].tolist()

                # Setting the current index of the lap selection combobox to that of the fastest lap
                self.lap_sel3.setCurrentIndex(fast_index[0])

            else:
                fastest_lap = self.current_session.laps.pick_driver(self.drivers[id]).pick_fastest()

                # Setting the current index of the lap selection combobox to that of the fastest lap
                self.lap_sel3.setCurrentIndex(int(fastest_lap['LapNumber']) - 1)
    
    # Setting the driver selection index to ~none~
    def clear_driver(self, id):
        if id == 0:           
            self.driver1.setCurrentIndex(-1)           
        elif id == 1:  
            self.driver2.setCurrentIndex(-1)
        elif id == 2:
            self.driver3.setCurrentIndex(-1)

    '''
    Clearing the data for the specific driver who's data needs to be cleared/reset
        id: index for which driver is being cleared
    '''
    def clear_driver_data(self, id):
        self.laps[id] = ''
        self.driver_laptimes_disp[id].clear()
        self.driver_sector1_disp[id].clear()
        self.driver_sector2_disp[id].clear()
        self.driver_sector3_disp[id].clear()
        self.tyre_compounds[id] = ''
        self.driver_laptimes[id] = ''
        self.driver_laps[id] = pd.DataFrame()

        self.speed_tel1[id].clear()
        self.speed1p_legend.removeItem(self.speed_tel1[id])
        self.speed_tel2[id].clear()
        self.speed2p_legend.removeItem(self.speed_tel2[id])

        self.brake_tel1[id].clear()
        self.brake1p_legend.removeItem(self.brake_tel1[id])
        self.brake_tel2[id].clear()
        self.brake2p_legend.removeItem(self.brake_tel2[id])

        self.rpm_tel1[id].clear()
        self.rpm1p_legend.removeItem(self.rpm_tel1[id])
        self.rpm_tel2[id].clear()
        self.rpm2p_legend.removeItem(self.rpm_tel2[id])

        self.throttle_tel1[id].clear()
        self.throttle1p_legend.removeItem(self.throttle_tel1[id])
        self.throttle_tel2[id].clear()
        self.throttle2p_legend.removeItem(self.throttle_tel2[id])
        
        self.ngear_tel1[id].clear()
        self.ngear1p_legend.removeItem(self.ngear_tel1[id])
        self.ngear_tel2[id].clear()
        self.ngear2p_legend.removeItem(self.ngear_tel2[id])

        self.drs_tel1[id].clear()
        self.drs1p_legend.removeItem(self.drs_tel1[id])
        self.drs_tel2[id].clear()
        self.drs2p_legend.removeItem(self.drs_tel2[id])

        self.driver_colors_disp[id].setStyleSheet('background-color: #28282a')

        if id == 0:                   
            self.driver1_compound.setIcon(QIcon())
        elif id == 1:          
            self.driver2_compound.setIcon(QIcon())
        elif id == 2:
            self.driver3_compound.setIcon(QIcon())
    '''
    LOADING ALL DRIVER COMPARISON DATA
        id: index for which driver is being updated
    Includes:
        Displaying Driver Color for identification
        Displaying Laptimes
        Displaying Sector Times
        Displaying Tyre compound used on the lap
        Plotting Telemetry Data
        Adding all the corner markers onto the telemetry display
        Plotting the Delta Time [with respect to the first driver in self.drivers array]
        Displaying the Track Domination based on selected Laps
    '''
    def load_compare_data(self, id):
       
        if self.initial_load:
            return

        # Clearing driver data only if plotted prior
        if not self.speed_tel1[id] == '':
            self.clear_driver_data(id)
        
        event = ff1.get_event(self.current_session.date.year, self.current_session.event['EventName'])

        # Finding the maximum circuit distance from geojson data
        with open('f1_circuits/maps/' + event['Location'] + '.geojson', 'r') as file:
            geo_data = geojson.load(file)
        for feature in geo_data['features']:
            self.circuit_distance = feature['properties']['length']
        
        # Initializing Laps array
        self.laps = [self.lap_sel1.currentText(), self.lap_sel2.currentText(), self.lap_sel3.currentText()]       
        self.display_lap_time(id)
        self.display_driv_color(id)
        self.plot_tel(id)
        self.plot_delta()
        self.plot_corner_markers()
        self.plot_track_domination()

        print(self.drivers)
        print(self.laps)
        print(self.tyre_compounds)
        print(self.driver_laptimes)

    '''
    Displaying the Driver Color indicator for selected driver
    ERROR: Currently shows no difference between teammates prior to the 2024 season due to the way FastF1 works
        id: index for which driver is being updated
    '''
    def display_driv_color(self, id):
        if not (self.drivers[id] == '0' or self.laps[id] == ''):
            driver_lap = self.driver_laps[id]              
            if self.current_session.date.year == 2024:
                if (getattr(self.current_session, 'name') == 'Qualifying' or 
                    getattr(self.current_session, 'name') == 'Sprint Qualifying' or 
                    getattr(self.current_session, 'name') == 'Sprint Shootout'):
                    driv_color = ff1.plotting.driver_color(driver_lap['Driver'])                    
                else:
                    driv_color = ff1.plotting.driver_color(driver_lap['Driver'].iat[0])               
            else:
                if (getattr(self.current_session, 'name') == 'Qualifying' or 
                    getattr(self.current_session, 'name') == 'Sprint Qualifying' or 
                    getattr(self.current_session, 'name') == 'Sprint Shootout'):
                    driv_color = ff1.plotting.team_color(driver_lap['Team'])
                else:
                    driv_color = ff1.plotting.team_color(driver_lap['Team'].iat[0])
            
            self.driver_colors_disp[id].setStyleSheet('background-color: ' + driv_color)

    '''
    Displays the Laptime & Sector times for the selected lap
        id: index for which driver is being updated
    '''
    def display_lap_time(self, id):
        if not (self.drivers[id] == '0' or self.laps[id] == ''):
            temp = re.findall(r'\b\d+\b', self.laps[id])           
            self.laps[id] = temp[0]

            # Generating the required arrays
            if (getattr(self.current_session, 'name') == 'Qualifying' or 
                getattr(self.current_session, 'name') == 'Sprint Qualifying' or 
                getattr(self.current_session, 'name') == 'Sprint Shootout'):
                driver_lap_temp = self.current_session.laps.pick_driver(self.drivers[id]).pick_wo_box()
                self.driver_laps[id] = driver_lap_temp.iloc[int(self.laps[id]) - 1]
                self.driver_laptimes[id] = self.driver_laps[id]['LapTime']
                self.driver_sector1_times[id] = self.driver_laps[id]['Sector1Time']
                self.driver_sector2_times[id] = self.driver_laps[id]['Sector2Time']
                self.driver_sector3_times[id] = self.driver_laps[id]['Sector3Time']
                self.tyre_compounds[id] = self.driver_laps[id]['Compound']
            else:
                self.driver_laps[id] = self.current_session.laps.pick_driver(self.drivers[id]).pick_lap(int(self.laps[id]))
                self.driver_laptimes[id] = self.driver_laps[id]['LapTime'].iat[0]
                self.tyre_compounds[id] = self.driver_laps[id]['Compound'].iat[0]
                self.driver_sector1_times[id] = self.driver_laps[id]['Sector1Time'].iat[0]
                self.driver_sector2_times[id] = self.driver_laps[id]['Sector2Time'].iat[0]
                self.driver_sector3_times[id] = self.driver_laps[id]['Sector3Time'].iat[0]

            # Converts timedelta object into a readable format for display
            # [Repeated for sector times]

            minutes = str(int(np.floor(self.driver_laptimes[id].seconds / 60)))
            seconds = str(int(self.driver_laptimes[id].seconds - (np.floor(self.driver_laptimes[id].seconds / 60) * 60)))
            seconds = seconds.zfill(2)
            microseconds = str(int(round(self.driver_laptimes[id].microseconds - (np.floor(self.driver_laptimes[id].microseconds / (6 * 10**7)) * (6 * 10**7)) - (np.floor(self.driver_laptimes[id].microseconds / (10**6)) * (10**6)), 3) / 1000))
            microseconds = microseconds.zfill(3)
                
            self.driver_laptimes[id] =  minutes + ' : ' + seconds + ' . ' + microseconds
            
            if (getattr(self.current_session, 'name') == 'Qualifying' or 
                getattr(self.current_session, 'name') == 'Sprint Qualifying' or 
                getattr(self.current_session, 'name') == 'Sprint Shootout'):
                minutes = str(int(np.floor(self.driver_sector1_times[id].seconds / 60)))
                seconds = str(int(self.driver_sector1_times[id].seconds - (np.floor(self.driver_sector1_times[id].seconds / 60) * 60)))
                seconds = seconds.zfill(2)
                microseconds = str(int(round(self.driver_sector1_times[id].microseconds - (np.floor(self.driver_sector1_times[id].microseconds / (6 * 10**7)) * (6 * 10**7)) - (np.floor(self.driver_sector1_times[id].microseconds / (10**6)) * (10**6)), 3) / 1000))
                microseconds = microseconds.zfill(3)

                self.driver_sector1_times[id] =  minutes + ':' + seconds + ':' + microseconds

            elif int(self.driver_laps[id]['LapNumber'].iloc[0]) == 1: 
                self.driver_sector1_times[id] =  'NaN'

            else:
                minutes = str(int(np.floor(self.driver_sector1_times[id].seconds / 60)))
                seconds = str(int(self.driver_sector1_times[id].seconds - (np.floor(self.driver_sector1_times[id].seconds / 60) * 60)))
                seconds = seconds.zfill(2)
                microseconds = str(int(round(self.driver_sector1_times[id].microseconds - (np.floor(self.driver_sector1_times[id].microseconds / (6 * 10**7)) * (6 * 10**7)) - (np.floor(self.driver_sector1_times[id].microseconds / (10**6)) * (10**6)), 3) / 1000))
                microseconds = microseconds.zfill(3)
                    
                self.driver_sector1_times[id] =  minutes + ':' + seconds + ':' + microseconds

            minutes = str(int(np.floor(self.driver_sector2_times[id].seconds / 60)))
            seconds = str(int(self.driver_sector2_times[id].seconds - (np.floor(self.driver_sector2_times[id].seconds / 60) * 60)))
            seconds = seconds.zfill(2)
            microseconds = str(int(round(self.driver_sector2_times[id].microseconds - (np.floor(self.driver_sector2_times[id].microseconds / (6 * 10**7)) * (6 * 10**7)) - (np.floor(self.driver_sector2_times[id].microseconds / (10**6)) * (10**6)), 3) / 1000))
            microseconds = microseconds.zfill(3)
                
            self.driver_sector2_times[id] =  minutes + ':' + seconds + ':' + microseconds

            minutes = str(int(np.floor(self.driver_sector3_times[id].seconds / 60)))
            seconds = str(int(self.driver_sector3_times[id].seconds - (np.floor(self.driver_sector3_times[id].seconds / 60) * 60)))
            seconds = seconds.zfill(2)
            microseconds = str(int(round(self.driver_sector3_times[id].microseconds - (np.floor(self.driver_sector3_times[id].microseconds / (6 * 10**7)) * (6 * 10**7)) - (np.floor(self.driver_sector3_times[id].microseconds / (10**6)) * (10**6)), 3) / 1000))
            microseconds = microseconds.zfill(3)
                
            self.driver_sector3_times[id] =  minutes + ':' + seconds + ':' + microseconds

            # Adding the variables to the labels
            self.driver_laptimes_disp[id].setText(self.driver_laptimes[id])
            self.driver_sector1_disp[id].setText(self.driver_sector1_times[id])
            self.driver_sector2_disp[id].setText(self.driver_sector2_times[id])
            self.driver_sector3_disp[id].setText(self.driver_sector3_times[id])

            # Setting the tyre compound used on the given lap
            self.display_tyre_compound(id)
    
    '''
    Displays the Tyre compound used for the selected lap as an image
        id: index for which driver is being updated
    '''
    def display_tyre_compound(self, id):
        tyre_compound_picture = QIcon('images/tyre_compounds/' + self.tyre_compounds[id] + '.png')
        if id == 0:
            self.driver1_compound.setIcon(tyre_compound_picture)
        elif id == 1:
            self.driver2_compound.setIcon(tyre_compound_picture)
        elif id == 2:
            self.driver3_compound.setIcon(tyre_compound_picture)

    # Plots the corner markers onto the telemetry display
    def plot_corner_markers(self):
        if not self.drivers == ['0','0','0']:
            for _, corners in self.circuit_info.corners.iterrows():
                    corner_line = pg.InfiniteLine(pos = corners['Distance'], angle = 90, movable= False, pen = 'grey')
                    text = f"{corners['Number']}{corners['Letter']}"
                    text = pg.TextItem(text, color= 'grey')
                    corner_line.setPen(width = 0.5, style = Qt.DotLine)
                    self.speed1p.addItem(corner_line)
                    self.speed1p.addItem(text)
                    text.setPos(corners['Distance'] + 10, 30)
                    corner_line = pg.InfiniteLine(pos = corners['Distance'], angle = 90, movable= False, pen = 'grey')
                    text = f"{corners['Number']}{corners['Letter']}"
                    text = pg.TextItem(text, color= 'grey')
                    corner_line.setPen(width = 0.5, style = Qt.DotLine)
                    self.speed2p.addItem(corner_line)
                    self.speed2p.addItem(text)
                    text.setPos(corners['Distance'] + 10, 30)

                    corner_line = pg.InfiniteLine(pos = corners['Distance'], angle = 90, movable= False, pen = 'grey')
                    text = f"{corners['Number']}{corners['Letter']}"
                    text = pg.TextItem(text, color= 'grey')
                    corner_line.setPen(width = 0.5, style = Qt.DotLine)
                    self.rpm1p.addItem(corner_line)
                    self.rpm1p.addItem(text)
                    text.setPos(corners['Distance'] + 10, 1200)
                    corner_line = pg.InfiniteLine(pos = corners['Distance'], angle = 90, movable= False, pen = 'grey')
                    text = f"{corners['Number']}{corners['Letter']}"
                    text = pg.TextItem(text, color= 'grey')
                    corner_line.setPen(width = 0.5, style = Qt.DotLine)
                    self.rpm2p.addItem(corner_line)
                    self.rpm2p.addItem(text)
                    text.setPos(corners['Distance'] + 10, 1200)

                    corner_line = pg.InfiniteLine(pos = corners['Distance'], angle = 90, movable= False, pen = 'grey')
                    text = f"{corners['Number']}{corners['Letter']}"
                    text = pg.TextItem(text, color= 'grey')
                    corner_line.setPen(width = 0.5, style = Qt.DotLine)
                    self.brake1p.addItem(corner_line)
                    self.brake1p.addItem(text)
                    text.setPos(corners['Distance'] + 10, 0.1)
                    corner_line = pg.InfiniteLine(pos = corners['Distance'], angle = 90, movable= False, pen = 'grey')
                    text = f"{corners['Number']}{corners['Letter']}"
                    text = pg.TextItem(text, color= 'grey')
                    corner_line.setPen(width = 0.5, style = Qt.DotLine)
                    self.brake2p.addItem(corner_line)
                    self.brake2p.addItem(text)
                    text.setPos(corners['Distance'] + 10, 0.1)

                    corner_line = pg.InfiniteLine(pos = corners['Distance'], angle = 90, movable= False, pen = 'grey')
                    text = f"{corners['Number']}{corners['Letter']}"
                    text = pg.TextItem(text, color= 'grey')
                    corner_line.setPen(width = 0.5, style = Qt.DotLine)
                    self.brake1p.addItem(corner_line)
                    self.brake1p.addItem(text)
                    text.setPos(corners['Distance'] + 10, 0.1)
                    corner_line = pg.InfiniteLine(pos = corners['Distance'], angle = 90, movable= False, pen = 'grey')
                    text = f"{corners['Number']}{corners['Letter']}"
                    text = pg.TextItem(text, color= 'grey')
                    corner_line.setPen(width = 0.5, style = Qt.DotLine)
                    self.brake2p.addItem(corner_line)
                    self.brake2p.addItem(text)
                    text.setPos(corners['Distance'] + 10, 0.1)

                    corner_line = pg.InfiniteLine(pos = corners['Distance'], angle = 90, movable= False, pen = 'grey')
                    text = f"{corners['Number']}{corners['Letter']}"
                    text = pg.TextItem(text, color= 'grey')
                    corner_line.setPen(width = 0.5, style = Qt.DotLine)
                    self.ngear1p.addItem(corner_line)
                    self.ngear1p.addItem(text)
                    text.setPos(corners['Distance'] + 10, 1.2)
                    corner_line = pg.InfiniteLine(pos = corners['Distance'], angle = 90, movable= False, pen = 'grey')
                    text = f"{corners['Number']}{corners['Letter']}"
                    text = pg.TextItem(text, color= 'grey')
                    corner_line.setPen(width = 0.5, style = Qt.DotLine)
                    self.ngear2p.addItem(corner_line)
                    self.ngear2p.addItem(text)
                    text.setPos(corners['Distance'] + 10, 1.2)

                    corner_line = pg.InfiniteLine(pos = corners['Distance'], angle = 90, movable= False, pen = 'grey')
                    text = f"{corners['Number']}{corners['Letter']}"
                    text = pg.TextItem(text, color= 'grey')
                    corner_line.setPen(width = 0.5, style = Qt.DotLine)
                    self.throttle1p.addItem(corner_line)
                    self.throttle1p.addItem(text)
                    text.setPos(corners['Distance'] + 10, 10)
                    corner_line = pg.InfiniteLine(pos = corners['Distance'], angle = 90, movable= False, pen = 'grey')
                    text = f"{corners['Number']}{corners['Letter']}"
                    text = pg.TextItem(text, color= 'grey')
                    corner_line.setPen(width = 0.5, style = Qt.DotLine)
                    self.throttle2p.addItem(corner_line)
                    self.throttle2p.addItem(text)
                    text.setPos(corners['Distance'] + 10, 10)

                    corner_line = pg.InfiniteLine(pos = corners['Distance'], angle = 90, movable= False, pen = 'grey')
                    text = f"{corners['Number']}{corners['Letter']}"
                    text = pg.TextItem(text, color= 'grey')
                    corner_line.setPen(width = 0.5, style = Qt.DotLine)
                    self.deltap.addItem(corner_line)
                    self.deltap.addItem(text)
                    text.setPos(corners['Distance'] + 10, 0.02)

                    corner_line = pg.InfiniteLine(pos = corners['Distance'], angle = 90, movable= False, pen = 'grey')
                    text = f"{corners['Number']}{corners['Letter']}"
                    text = pg.TextItem(text, color= 'grey')
                    corner_line.setPen(width = 0.5, style = Qt.DotLine)
                    self.drs1p.addItem(corner_line)
                    self.drs1p.addItem(text)
                    text.setPos(corners['Distance'] + 10, 0.02)

                    corner_line = pg.InfiniteLine(pos = corners['Distance'], angle = 90, movable= False, pen = 'grey')
                    text = f"{corners['Number']}{corners['Letter']}"
                    text = pg.TextItem(text, color= 'grey')
                    corner_line.setPen(width = 0.5, style = Qt.DotLine)
                    self.drs2p.addItem(corner_line)
                    self.drs2p.addItem(text)
                    text.setPos(corners['Distance'] + 10, 0.02)

    '''
    Plotting the driver Telemetry for the given lap
        id: index for which driver is being updated
    '''
    def plot_tel(self, id):
        # Checking if the selected driver or lap is blank
        if not (self.drivers[id] == '0'or self.laps[id] == ''):
            driver_lap = self.driver_laps[id]
            driver_tel = driver_lap.get_car_data().add_distance()

            # Finding the driver color & generating the telemetry data for the selected driver's lap
            # [Currently has the same error as display_driver_color]
            if self.current_session.date.year == 2024:
                if (getattr(self.current_session, 'name') == 'Qualifying' or 
                    getattr(self.current_session, 'name') == 'Sprint Qualifying' or 
                    getattr(self.current_session, 'name') == 'Sprint Shootout'):
                    driv_color = ff1.plotting.driver_color(driver_lap['Driver'])
                    driver_name = driver_lap['Driver']
                else:
                    driv_color = ff1.plotting.driver_color(driver_lap['Driver'].iat[0])
                    driver_name = driver_lap['Driver'].iat[0]

                    if int(driver_lap['LapNumber'].iloc[0]) == 1:
                        temp_lap = self.current_session.laps.pick_fastest()
                        temp_tel = temp_lap.get_telemetry().add_distance()
                        driver_tel['Distance'] = driver_tel['Distance'] + (temp_tel['Distance'].max() - driver_tel['Distance'].max())
            
            else:
                if (getattr(self.current_session, 'name') == 'Qualifying' or 
                    getattr(self.current_session, 'name') == 'Sprint Qualifying' or 
                    getattr(self.current_session, 'name') == 'Sprint Shootout'):
                    driv_color = ff1.plotting.team_color(driver_lap['Team'])
                    driver_name = driver_lap['Driver']
                else:
                    driv_color = ff1.plotting.team_color(driver_lap['Team'].iat[0])
                    driver_name = driver_lap['Driver'].iat[0]

                    if int(driver_lap['LapNumber'].iloc[0]) == 1:
                        temp_lap = self.current_session.laps.pick_fastest()
                        temp_tel = temp_lap.get_telemetry().add_distance()
                        driver_tel['Distance'] = driver_tel['Distance'] + (temp_tel['Distance'].max() - driver_tel['Distance'].max())
                
            max_d = self.circuit_distance             
            
            # Plotting all the generated data while constructing an array of it for better management
            self.speed_tel1[id] = self.speed1p.plot(driver_tel['Distance'], driver_tel['Speed'], pen = pg.mkPen(driv_color, width= 2.5), name=driver_name)
            self.brake_tel1[id] = self.brake1p.plot(driver_tel['Distance'], driver_tel['Brake'], pen = pg.mkPen(driv_color, width= 2.5), name=driver_name)
            self.rpm_tel1[id] = self.rpm1p.plot(driver_tel['Distance'], driver_tel['RPM'], pen = pg.mkPen(driv_color, width= 2.5), name=driver_name)
            self.throttle_tel1[id] = self.throttle1p.plot(driver_tel['Distance'], driver_tel['Throttle'], pen = pg.mkPen(driv_color, width= 2.5), name=driver_name)
            self.ngear_tel1[id] = self.ngear1p.plot(driver_tel['Distance'], driver_tel['nGear'], pen = pg.mkPen(driv_color, width= 2.5), name=driver_name)
            self.drs_tel1[id] = self.drs1p.plot(driver_tel['Distance'], driver_tel['DRS'], pen = pg.mkPen(driv_color, width= 2.5), name=driver_name)

            self.speed_tel2[id] = self.speed2p.plot(driver_tel['Distance'], driver_tel['Speed'], pen = pg.mkPen(driv_color, width= 2.5), name=driver_name)
            self.brake_tel2[id] = self.brake2p.plot(driver_tel['Distance'], driver_tel['Brake'], pen = pg.mkPen(driv_color, width= 2.5), name=driver_name)
            self.rpm_tel2[id] = self.rpm2p.plot(driver_tel['Distance'], driver_tel['RPM'], pen = pg.mkPen(driv_color, width= 2.5), name=driver_name)
            self.throttle_tel2[id] = self.throttle2p.plot(driver_tel['Distance'], driver_tel['Throttle'], pen = pg.mkPen(driv_color, width= 2.5), name=driver_name)
            self.ngear_tel2[id] = self.ngear2p.plot(driver_tel['Distance'], driver_tel['nGear'], pen = pg.mkPen(driv_color, width= 2.5), name=driver_name)
            self.drs_tel2[id] = self.drs2p.plot(driver_tel['Distance'], driver_tel['DRS'], pen = pg.mkPen(driv_color, width= 2.5), name=driver_name)

            # Setting the telemetry plot dimensions and scrollable limits
            self.speed1p.getViewBox().setLimits(xMin=0, xMax=max_d, yMin=0, yMax=360)
            self.speed2p.getViewBox().setLimits(xMin=0, xMax=max_d, yMin=0, yMax=360)
            self.rpm1p.getViewBox().setLimits(xMin=0, xMax=max_d, yMin=0, yMax=14100)
            self.rpm2p.getViewBox().setLimits(xMin=0, xMax=max_d, yMin=0, yMax=14100)
            self.brake1p.getViewBox().setLimits(xMin=0, xMax=max_d, yMin=0, yMax=1.10)
            self.brake2p.getViewBox().setLimits(xMin=0, xMax=max_d, yMin=0, yMax=1.10)
            self.throttle1p.getViewBox().setLimits(xMin=0, xMax=max_d, yMin=0, yMax=110)
            self.throttle2p.getViewBox().setLimits(xMin=0, xMax=max_d, yMin=0, yMax=110)
            self.ngear1p.getViewBox().setLimits(xMin=0, xMax=max_d, yMin=0, yMax=8.5)
            self.ngear2p.getViewBox().setLimits(xMin=0, xMax=max_d, yMin=0, yMax=8.5)
            self.drs1p.getViewBox().setLimits(xMin=0, xMax=max_d, yMin=7.5, yMax=14.5)
            self.drs2p.getViewBox().setLimits(xMin=0, xMax=max_d, yMin=7.5, yMax=14.5)

    '''
    Plotting the driver delta time
    [works only when 2 or more driver laps were selected]
    '''
    def plot_delta(self):
        max_d = self.circuit_distance

        # Checking the number of blank lap selection combo boxes 
        # [i.e. how many driver laps were selected]
        ele = ''
        x = [i for i in self.laps if i==ele]
        self.deltap.clear()

        # Plotting Delta Time only if 2 or more driver laps were selected
        if not len(x) >= 2:
            # Adding horizontal line at delta time = 0s
            self.deltap.addLine(y = 0, pen = pg.mkPen('white', width= 2))
            driver_count = 0
            for id in range(3):
                if not (self.drivers[id] == '0'or self.laps[id] == ''):
                    # Setting the first driver lap selected/available as the reference telemetry
                    if driver_count == 0:
                        ref_lap = self.driver_laps[id]
                        ref_tel = ref_lap.get_telemetry()
                        if (getattr(self.current_session, 'name') == 'Qualifying' or 
                            getattr(self.current_session, 'name') == 'Sprint Qualifying' or 
                            getattr(self.current_session, 'name') == 'Sprint Shootout'):
                            ref_name = ref_lap['Driver']
                        else:
                            ref_name = ref_lap['Driver'].iat[0]
                        driver_count = driver_count + 1
                        continue
                    
                    # Finding the delta time of the following laps with respect to the first
                    else:
                        driver_lap = self.driver_laps[id]
                        driver_tel = driver_lap.get_telemetry()

                        if self.current_session.date.year == 2024:
                            if (getattr(self.current_session, 'name') == 'Qualifying' or 
                                getattr(self.current_session, 'name') == 'Sprint Qualifying' or 
                                getattr(self.current_session, 'name') == 'Sprint Shootout'):
                                driv_color = ff1.plotting.driver_color(driver_lap['Driver'])
                                driver_name = driver_lap['Driver']
                            else:
                                driv_color = ff1.plotting.driver_color(driver_lap['Driver'].iat[0])
                                driver_name = driver_lap['Driver'].iat[0]
                            
                        else:
                            if (getattr(self.current_session, 'name') == 'Qualifying' or 
                                getattr(self.current_session, 'name') == 'Sprint Qualifying' or 
                                getattr(self.current_session, 'name') == 'Sprint Shootout'):
                                driv_color = ff1.plotting.team_color(driver_lap['Team'])
                                driver_name = driver_lap['Driver']
                            else:
                                driv_color = ff1.plotting.team_color(driver_lap['Team'].iat[0])
                                driver_name = driver_lap['Driver'].iat[0]

                    # Extracting the delta time
                    delta_time, ref_dist = self.get_delta(ref_tel, driver_tel)

                    # Finding the limits of the arrays; required for setting plot limits
                    if driver_count == 1:
                            max = delta_time.max()
                            min = delta_time.min()
                        
                    else:
                        if delta_time.max() > max:
                            max = delta_time.max()
                        if delta_time.min() < min:
                            min = delta_time.min()

                    driver_count = driver_count + 1
                    self.deltap.plot(ref_dist, delta_time, pen = pg.mkPen(driv_color, width= 2.5), name=driver_name)

            self.deltap.getViewBox().setLimits(xMin=0, xMax=max_d, yMin= min - 0.1, yMax= max + 0.1)
            self.deltap.setLabel('left', 'Gap to ' + ref_name, units ='s')
            self.deltap.setLabel('bottom', 'Distance', units ='km')

    '''
    Calculating the Delta time w.r.t telemetry distance between two laps using interpolation
    [self-made function due to the deprecation of the FastF1 utils module]
    '''
    def get_delta(self, ref_lap, comp_lap):
        
        distance_ref = ref_lap['Distance']
        distance_comp = comp_lap['Distance']
        time_ref = [0] * len(ref_lap['Time'])
        time_comp = [0] * len(comp_lap['Time'])

        # Converting Laptime column into a useful format (microseconds)
        for i in range(len(ref_lap['Time'])):
            time_ref[i] = ref_lap['Time'].iloc[i].seconds * (10 ** 6) + ref_lap['Time'].iloc[i].microseconds

        for i in range(len(comp_lap['Time'])):
            time_comp[i] = comp_lap['Time'].iloc[i].seconds * (10 ** 6) + comp_lap['Time'].iloc[i].microseconds

        # Setting the final distances the same in order to make a useful interpolation
        # [ERROR: Causes a sharp spike towards the end of the plot, as well as some error in the leadup to it]
        max1 = distance_comp.max()
        max2 = distance_ref.max()
        if distance_comp.max() < distance_ref.max():
            distance_comp.replace(to_replace= max1, value=max2, inplace=True)
        elif distance_comp.max() > distance_ref.max():
            distance_ref.replace(to_replace=max2, value=max1, inplace=True)

        # Setting the initial distance counter as 0
        distance_comp.replace(distance_comp.min(), 0, inplace=True)
        distance_ref.replace(distance_ref.min(), 0, inplace=True)

        # 1-D Interpolation of data for plotting
        temp = interpolate.interp1d(distance_ref, time_ref) 
        distance_ref = np.arange(distance_ref.min(), distance_ref.max()) 
        time_ref = temp(distance_ref) 

        temp = interpolate.interp1d(distance_comp, time_comp) 
        distance_comp = np.arange(distance_comp.min(), distance_comp.max()) 
        time_comp = temp(distance_comp)

        # Generating array of delta time at different points based on the interpolated data
        delta = (time_ref - time_comp) / (10** 6)
        return(delta, distance_ref)

    # Plotting Track Domination for the selected driver laps
    def plot_track_domination(self):
        driver_count = 0
        for i, driver in enumerate(self.drivers):
            if not self.laps[i] == '':
                driver_lap = self.driver_laps[i]
                driver_tel = driver_lap.get_telemetry().add_distance()
                if self.current_session.date.year == 2024:
                    if (getattr(self.current_session, 'name') == 'Qualifying' or 
                        getattr(self.current_session, 'name') == 'Sprint Qualifying' or 
                        getattr(self.current_session, 'name') == 'Sprint Shootout'):
                        driv_color = ff1.plotting.driver_color(driver_lap['Driver'])
                    else:
                        driv_color = ff1.plotting.driver_color(driver_lap['Driver'].iat[0])

                        if int(driver_lap['LapNumber'].iloc[0]) == 1:
                            temp_lap = self.current_session.laps.pick_fastest()
                            temp_tel = temp_lap.get_telemetry().add_distance()
                            driver_tel['Distance'] = driver_tel['Distance'] + (temp_tel['Distance'].max() - driver_tel['Distance'].max())
                
                else:
                    if (getattr(self.current_session, 'name') == 'Qualifying' or 
                        getattr(self.current_session, 'name') == 'Sprint Qualifying' or 
                        getattr(self.current_session, 'name') == 'Sprint Shootout'):
                        driv_color = ff1.plotting.team_color(driver_lap['Team'])
                    else:
                        driv_color = ff1.plotting.team_color(driver_lap['Team'].iat[0])

                        if int(driver_lap['LapNumber'].iloc[0]) == 1:
                            temp_lap = self.current_session.laps.pick_fastest()
                            temp_tel = temp_lap.get_telemetry().add_distance()
                            driver_tel['Distance'] = driver_tel['Distance'] + (temp_tel['Distance'].max() - driver_tel['Distance'].max())
                
                driver_tel['Driver'] = self.drivers[i]
                driver_tel['DriverColor'] = driv_color

                # Generating array of telemetry data
                if i == 0:
                    telemetry = driver_tel
                else:
                    if driver_count == 0:
                        telemetry = driver_tel
                    else:
                        telemetry = telemetry._append(driver_tel)
                
                driver_count = driver_count + 1

        if not (self.drivers == ['0', '0', '0'] or self.laps == ['','','']):
            # Generate equally sized mini-sectors 
            num_minisectors = 18
            minisector_length = self.circuit_distance / num_minisectors

            # Initiate minisector variable, with 0 (meters) as a starting point.
            minisectors = [0]

            # Add multiples of minisector_length to the minisectors
            for i in range(0, (num_minisectors - 1)):
                minisectors.append(minisector_length * (i + 1))
            
            # Adding the minisector column to the dataframe 
            # [i.e. in which minisector was the telemetry data for the lap at that point recorded]
            telemetry['Minisector'] = telemetry['Distance'].apply(
                lambda dist: (
                    int((dist // minisector_length) + 1)
                )
            )

            # Initializing the arrays to be used in the loop
            drivers = [None] * driver_count
            delta = [None] * driver_count

            for i in range(1, num_minisectors + 1):
                # Temporary dataframe of the selected minisector
                filtered_data = telemetry[telemetry['Minisector'] == i].iloc[:, :] 

                # Collapsing the dataframe into just a single entry for each driver
                # [Done by finding the average speed carried through the minisector by the driver & resetting index]
                msector_dom = filtered_data.groupby(['Minisector', 'Driver', 'DriverColor'])['Speed'].mean().reset_index()

                # Generating driver array & delta time array for each minisector
                for id in range(driver_count):
                    drivers[id] = filtered_data[filtered_data['Driver'] == msector_dom['Driver'].iloc[id]].iloc[:, :]
                    delta[id] = drivers[id]['Time'].max() - drivers[id]['Time'].min()
                
                # Adding the delta time points to the required dataframe
                msector_dom = msector_dom.assign(Time = delta)
                if i == 1:
                    times = msector_dom
                else:
                    times = times._append(msector_dom)

            # Resetting the index of the modified dataframe
            times = times.reset_index()
            times.drop(["index"], axis = 1, inplace = True)

            # Grouping by Minisector & selecting the minimum elapsed time for each
            fastest_driver = times.loc[times.groupby(['Minisector'])['Time'].idxmin()]
            # Getting rid of the speed column and renaming the driver column
            fastest_driver = fastest_driver[['Minisector', 'Driver', 'DriverColor']].rename(columns={'Driver': 'FastestDriver'})

            track = telemetry.loc[:, ('X', 'Y')].to_numpy()

            # Convert the rotation angle from degrees to radian.
            track_angle = self.circuit_info.rotation / 180 * np.pi

            # Rotate and plot the track map.
            track = self.rotate(track, angle=track_angle)

            # Adding Starting line marker
            start_line = pg.ScatterPlotItem(size=20, pen = pg.mkPen('k' , width= 8), brush=pg.mkBrush(255, 255, 255), symbol = 'o')
            start_line.addPoints([track[0][0]], [track[0][1]])

            self.track_dom_p.clear()
            track = np.array_split(track, num_minisectors)
            for i in range(num_minisectors):
                self.track_dom_p.plot(track[i][:, 0], track[i][:, 1], pen = pg.mkPen(fastest_driver['DriverColor'].iloc[i] ,width= 15))
            self.track_dom_p.addItem(start_line)
            self.plot_corner_points()

    # Rotation function for plotting track layout in official rotation
    def rotate(self, xy, *, angle):
        rot_mat = np.array([[np.cos(angle), np.sin(angle)],
                            [-np.sin(angle), np.cos(angle)]])
        return np.matmul(xy, rot_mat)
    
    # Plotting the Corner points on Track Domination Widget
    def plot_corner_points(self):
        offset_vector = [500, 0]
        track_angle = self.circuit_info.rotation / 180 * np.pi
        for _, corner in self.circuit_info.corners.iterrows():
            # Create a string from corner number and letter
            txt = pg.TextItem((f"{corner['Number']}{corner['Letter']}"), anchor=(0.5,0))

            # Convert the angle from degrees to radian.
            offset_angle = corner['Angle'] / 180 * np.pi

            # Rotate the offset vector so that it points sideways from the track.
            offset_x, offset_y = self.rotate(offset_vector, angle=offset_angle)

            # Add the offset to the position of the corner
            text_x = corner['X'] + offset_x
            text_y = corner['Y'] + offset_y

            # Rotate the text position equivalently to the rest of the track map
            text_x, text_y = self.rotate([text_x, text_y], angle=track_angle)

            # Finally, print the corner number inside the circle.
            self.track_dom_p.addItem(txt)
            txt.setPos(text_x, text_y)
