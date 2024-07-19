''' ALL APP LIBRARY IMPORTS AND MODIFICATIONS'''
# PyQt5
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout, QButtonGroup, QShortcut, QStyledItemDelegate
from PyQt5 import QtWidgets as qtw
import PyQt5.QtGui as QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import * 
from PyQt5.QtCore import QPoint, QRect, QSize, Qt
from PyQt5.QtGui import QIcon, QIconEngine, QImage, QPainter, QPixmap
from PyQt5.uic import loadUi 
from PyQt5.QtCore import Qt as QtCore

# Miscellanous Functionality
import sys
import os
from datetime import timezone, timedelta
import datetime
import socket

# FastF1 API
import fastf1 as ff1
from fastf1 import plotting
from fastf1 import utils

# Plotting Libraries
import pyqtgraph as pg
from matplotlib import font_manager
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as  FigureCanvas
from matplotlib.collections import LineCollection
import matplotlib.animation as animation
import geojson

pg.setConfigOption('background', '#1e1e1f')

# FastF1 Plotting Global Modifications
ff1.plotting.DRIVER_COLORS['max verstappen'] = '#734fff'
ff1.plotting.DRIVER_COLORS['lewis hamilton'] = '#eef12e'
ff1.plotting.DRIVER_COLORS['sergio perez'] = '#1017df'
ff1.plotting.TEAM_COLORS['red bull'] = '#734fff'
ff1.plotting.DRIVER_COLORS['alexander albon'] = '#49BBFF'
ff1.plotting.DRIVER_COLORS['logan sargeant'] = '#008BFE'
ff1.plotting.TEAM_COLORS['williams'] = '#49BBFF'

ff1.plotting.setup_mpl(mpl_timedelta_support=True, color_scheme='fastf1', misc_mpl_mods=True)
font_dirs = ['/Users/niratpai/Library/Fonts']
font_files = font_manager.findSystemFonts(fontpaths=font_dirs)
for font_file in font_files:
    font_manager.fontManager.addfont(font_file)
plt.rcParams['font.family'] = 'Formula1'

# Data Analysis Libraries
import numpy as np
import pandas as pd
import re
from scipy import interpolate 

# Setting Cache Directory
ff1.Cache.enable_cache('cache')

# Rewriting the Icon Map Engine for higher resolution Images & Icons [affects the sidebar]
class PixmapIconEngine(QIconEngine):
    def __init__(self, iconPath: str):
        self.iconPath = iconPath
        super().__init__()

    def paint(self, painter: QPainter, rect: QRect, mode: QIcon.Mode, state: QIcon.State):
        painter.setRenderHints(QPainter.Antialiasing |
                               QPainter.SmoothPixmapTransform)
        painter.drawImage(rect, QImage(self.iconPath))

    def pixmap(self, size: QSize, mode: QIcon.Mode, state: QIcon.State) -> QPixmap:
        pixmap = QPixmap(size)
        pixmap.fill(Qt.transparent)
        self.paint(QPainter(pixmap), QRect(QPoint(0, 0), size), mode, state)
        return pixmap

# Custom widget container for all matplotlib graphs involving the Track Layout
class SpeedVis(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        '''
        General plot parameters for every occurence of matplotlib widget integration
        '''
        self.fig = Figure(figsize=(10, 5))       
        self.can = FigureCanvas(self.fig)
        layout = QVBoxLayout(self)
        layout.addWidget(self.can)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.fig.set_facecolor('#171718')
        self.ax = self.fig.add_subplot()
        self.ax.set_xticklabels([])
        self.ax.set_yticklabels([])
        self.ax.set_facecolor('#171718')
        self.ax.tick_params(left = False, bottom = False)
        plt.setp(self.ax.spines.values(), lw=0)
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0.1)

    '''
    Plotting the speed visualization for a given lap
    [Code taken from: 
        https://docs.fastf1.dev/examples_gallery/plot_speed_on_track.html#sphx-glr-examples-gallery-plot-speed-on-track-py]
    '''
    def plot_visual(self, lap):
        colormap = mpl.cm.plasma                # selecting colormap for speed visualization
        self.x = lap.telemetry['X']             # values for x-axis
        self.y = lap.telemetry['Y']             # values for y-axis
        color = lap.telemetry['Speed']          # value to base color gradient on
        points = np.array([self.x, self.y]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)

        # Creating solid black background track line
        self.plot = self.ax.plot(lap.telemetry['X'], lap.telemetry['Y'],
                color='black', linestyle='-', linewidth=8, zorder=0)

        # Creating a continuous normalization to map data points to colors
        norm = plt.Normalize(color.min(), color.max())
        lc = LineCollection(segments, cmap=colormap, norm=norm, linestyle='-', linewidth=2)

        # Setting the values used for colormapping
        lc.set_array(color)

        # Merging all line segments together
        self.ax.add_collection(lc)

        # Setting the colorbar as the legend
        self.cbaxes = self.fig.add_axes([0.25, 0.1, 0.5, 0.05])
        normlegend = mpl.colors.Normalize(vmin=color.min(), vmax=color.max())
        self.legend = mpl.colorbar.ColorbarBase(self.cbaxes, norm=normlegend, cmap=colormap, orientation="horizontal")
        self.ax.set_facecolor('#171718')
        self.ax.axis('equal')

    '''
    Plotting the track domination for a given set of drivers
    References the code for plotting the Gear Shifts Visualization on track from FastF1:
        https://docs.fastf1.dev/examples_gallery/plot_gear_shifts_on_track.html
    '''
    def plot_dom(self, telemetry, driver_numbers, driver_colors):
        x = np.array(telemetry['X'].values)
        y = np.array(telemetry['Y'].values)

        points = np.array([x, y]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)
        fastest_driver_array = telemetry['Fastest_driver'].to_numpy().astype(float)

        driver_numbers = [float(driver_numbers) for driver_numbers in driver_numbers]
        #driver_numbers = [i for i in driver_numbers if i != 0]
        swap_index = np.argsort(driver_numbers)
        driver_numbers = sorted(driver_numbers)

        # fix sorting colors
        temp_array = driver_colors.copy() 
        for i, color in enumerate(driver_colors):
            temp_array[i] = driver_colors[swap_index[i]]

        driver_colors = temp_array

        if driver_colors[0] == 'white':
            del driver_colors[0]
        if driver_numbers[0] == 0:
            del driver_numbers[0]

        norm=plt.Normalize(min(driver_numbers),max(driver_numbers))
        cmap_list = list(zip(map(norm, driver_numbers), driver_colors))
        cmap = mpl.colors.LinearSegmentedColormap.from_list("", cmap_list)
        lc_comp = LineCollection(segments,  cmap=cmap, linewidth=4)
        lc_comp.set_array(fastest_driver_array)
        lc_comp.set_linewidth(3)

        self.ax.add_collection(lc_comp)
        self.ax.set_facecolor('#171718')
        self.ax.axis('equal')

    '''
    Plotting the corner markers for the track map
    '''
    def plot_corners(self, circuit_info):
        # offset length chosen arbitrarily to 'look good'
        offset_vector = [500, 0]

        # Converting the rotation angle from degrees to radian.
        track_angle = circuit_info.rotation / 180 * np.pi

        # Iterating over all corners.
        for _, corner in circuit_info.corners.iterrows():
            # Create a string from corner number and letter
            txt = f"{corner['Number']}{corner['Letter']}"

            # Convert the angle from degrees to radian.
            offset_angle = corner['Angle'] / 180 * np.pi

            # Rotating the offset vector so that it points sideways from the track.
            offset_x, offset_y = self.rotate(offset_vector, angle=offset_angle)

            # Adding the offset to the position of the corner
            text_x = corner['X'] + offset_x
            text_y = corner['Y'] + offset_y

            track_x = corner['X']
            track_y = corner['Y']

            # Encapsulating the text in a circle and pointing to the corner on track
            self.ax.scatter(text_x, text_y, color='#464646', s=100)
            self.ax.plot([track_x, text_x], [track_y, text_y], color='#464646')

            self.ax.text(text_x, text_y, txt,
                    va='center_baseline', ha='center', size='x-small', color='white')

    def rotate(self, xy, *, angle):
        rot_mat = np.array([[np.cos(angle), np.sin(angle)], [-np.sin(angle), np.cos(angle)]])
        return np.matmul(xy, rot_mat)

    ''''
    Function for clearing the figure for replotting [OR] for resetting all data
    '''
    def clear_visual(self):
        self.fig.clear()
        self.ax = self.fig.add_subplot()
        self.ax.set_xticklabels([])
        self.ax.set_yticklabels([])
        self.ax.set_facecolor('#171718')
        self.ax.tick_params(left = False, bottom = False)
        plt.setp(self.ax.spines.values(), lw=0)
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0.1)
 
class ui(QMainWindow):
    def __init__(self, parent = None):
        super(ui, self).__init__()

        loadUi('main_window.ui', self)

        # Stylizing the QComboBoxes with the applied QSS in .ui file
        self.grandprix_select.setItemDelegate(QStyledItemDelegate(self.grandprix_select))
        self.session_select.setItemDelegate(QStyledItemDelegate(self.session_select))
        self.driver1.setItemDelegate(QStyledItemDelegate(self.driver1))
        self.driver2.setItemDelegate(QStyledItemDelegate(self.driver2))
        self.driver3.setItemDelegate(QStyledItemDelegate(self.driver3))
        self.lap_sel1.setItemDelegate(QStyledItemDelegate(self.lap_sel1))
        self.lap_sel2.setItemDelegate(QStyledItemDelegate(self.lap_sel2))
        self.lap_sel3.setItemDelegate(QStyledItemDelegate(self.lap_sel3))
  
        self.setWindowTitle('F1 Data Analysis')

        '''
        TASK BAR MODIFICATIONS
        '''
        self.setUnifiedTitleAndToolBarOnMac(True)
        self.setAttribute(Qt.WA_TranslucentBackground)
        '''
        KEYBOARD SHORTCUTS
        Indludes:
            Cmd+W:  closing the app
            Cmd+F:  full screen
            Esc:    returning back to normal size while in full screen
            Cmd+M:  minimizing the app
        '''
        shortcut_close = QKeySequence(Qt.CTRL + Qt.Key_W)
        self.shortcut_close = QShortcut(shortcut_close, self)
        self.shortcut_close.activated.connect(lambda: self.close())

        shortcut_fullscrn = QKeySequence(Qt.CTRL + Qt.Key_F)
        self.shortcut_fullscrn = QShortcut(shortcut_fullscrn, self)
        self.shortcut_fullscrn.activated.connect(lambda: self.showFullScreen())

        shortcut_normal = QKeySequence(Qt.Key_Escape)
        self.shortcut_normal = QShortcut(shortcut_normal, self)
        self.shortcut_normal.activated.connect(lambda: self.showNormal())

        shortcut_minimize = QKeySequence(Qt.CTRL + Qt.Key_M)
        self.shortcut_minimize = QShortcut(shortcut_minimize, self)
        self.shortcut_minimize.activated.connect(lambda: self.showMinimized())

        # Switching to the required tile/Stacked Widget
        tabs = [self.home, self.standings, self.comparison, self.session_info, self.settings]
        self.tabs = QButtonGroup()

        for i in range(len(tabs)):
            self.tabs.addButton(tabs[i], i)
        
        self.tabs.buttonClicked.connect(self.switch_tabs)

        # Disabling Mouse scrolling on all combo-boxes
        opts = QtCore.FindChildrenRecursively
        comboboxes = self.findChildren(qtw.QComboBox, options=opts)
        for box in comboboxes:
            box.wheelEvent = lambda *event: None
            
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

        # Adding & setting all the Plot Layouts
        self.track_dom_layout = QHBoxLayout()
        self.track_dom_canvas = SpeedVis()
        self.track_dom_layout.setContentsMargins(0,0,0,0)
        self.track_dom_layout.addWidget(self.track_dom_canvas)
        self.track_domination.setLayout(self.track_dom_layout)
        self.set_plot_displays()

        # Loading the Session
        self.year = self.year_select.value()
        self.grand_prix = self.grandprix_select.currentText()
        self.count = 0
        # Populating Current Grand-Prix Selection ComboBox
        self.weekend_enable()

        # Year Selection
        self.year_select.valueChanged.connect(self.weekend_enable)
        # Race Selection
        self.grandprix_select.activated.connect(self.session_enable)
        # Session Selection
        self.session_select.activated.connect(self.drivers_select)

        # Loading laps for each selected driver
        self.driver1.currentIndexChanged.connect(lambda: self.laps_select(0))
        self.driver2.currentIndexChanged.connect(lambda: self.laps_select(1))
        self.driver3.currentIndexChanged.connect(lambda: self.laps_select(2))

        # Clearing Driver Data
        self.clear1.clicked.connect(lambda: self.clear_driver(0))
        self.clear2.clicked.connect(lambda: self.clear_driver(1))
        self.clear3.clicked.connect(lambda: self.clear_driver(2))

        # Setting the fastest lap of selected drivers
        self.fast1.clicked.connect(lambda: self.set_fastest_lap(0))
        self.fast2.clicked.connect(lambda: self.set_fastest_lap(1))
        self.fast3.clicked.connect(lambda: self.set_fastest_lap(2))   
        
        # Loading Data
        self.lap_sel1.currentIndexChanged.connect(lambda: self.load_compare_data(0))
        self.lap_sel2.currentIndexChanged.connect(lambda: self.load_compare_data(1))
        self.lap_sel3.currentIndexChanged.connect(lambda: self.load_compare_data(2))

        # Exporting Data
        self.export_data.clicked.connect(self.export)

    def switch_tabs(self):
        id = self.tabs.checkedId()
        self.stackedWidget.setCurrentIndex(id)

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

    # Clearing all the data loaded while switching Sessions, Weekends, or Seasons
    def clear_data(self):
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
        self.throttle1p.clear()
        self.brake1p.clear()
        self.brake2p.clear()
        self.ngear1p.clear()
        self.ngear2p.clear()
        self.drs1p.clear()
        self.drs2p.clear()

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

        self.track_dom_canvas.clear_visual()
        self.track_dom_canvas.can.draw()

        for i in range(len(self.driver_laptimes_disp)):
            self.driver_laptimes_disp[i].clear()
            self.driver_sector1_disp[i].clear()
            self.driver_sector2_disp[i].clear()
            self.driver_sector3_disp[i].clear()    
            self.driver_colors_disp[i].setStyleSheet('background-color: #28282a') 
    
    '''
    Clearing the data for the specific driver who's data needs to be cleared/reset
        id: index for which driver is being cleared
    '''
    def clear_driver_data(self, id):
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

        self.driver_colors_disp[id].setStyleSheet('background-color: rgb(30,30,30)')

        if id == 0:                   
            self.driver1_compound.setIcon(QIcon())
        elif id == 1:          
            self.driver2_compound.setIcon(QIcon())
        elif id == 2:
            self.driver3_compound.setIcon(QIcon())

    # Setting the driver selection index to ~none~
    def clear_driver(self, id):
        if id == 0:           
            self.driver1.setCurrentIndex(-1)           
        elif id == 1:  
            self.driver2.setCurrentIndex(-1)
        elif id == 2:
            self.driver3.setCurrentIndex(-1)

    # Filling the combo box with the list of Grand-Prix's of the selected Season
    def weekend_enable(self):
        self.clear_data()
        self.export_data.setEnabled(False)
        self.driver1.setEnabled(False)
        self.driver2.setEnabled(False)
        self.driver3.setEnabled(False)
        self.clear1.setEnabled(False)
        self.clear2.setEnabled(False)
        self.clear3.setEnabled(False)
        self.grandprix_select.clear()
        self.session_select.clear()

        # Getting the schedule for the given year
        self.year = self.year_select.value()
        schedule = ff1.get_event_schedule(self.year, include_testing=False)
        rounds = len(schedule) + 1

        for round in range(1, rounds):            
            event = schedule.get_event_by_round(round)

            # Checking the current time of running [the time the app was opened]
            self.current_time = datetime.datetime.now(timezone.utc)
            self.current_utc_time = self.current_time.replace(tzinfo=timezone.utc)
            grandprix_time = event.get_session_date('Practice 1',utc= True)
            grandprix_time = grandprix_time.replace(tzinfo=timezone.utc)

            # Checking if the weekend has started yet
            if (grandprix_time + timedelta(hours= 5)) < self.current_utc_time:
                self.grandprix_select.addItem(event['EventName'])
    
    # Filling the combo box with the list of Sessions for the selected Grand-Prix weekend
    def session_enable(self):
        self.session_select.clear()
        self.clear_data()
        self.export_data.setEnabled(False)
        self.driver1.setEnabled(False)
        self.driver2.setEnabled(False)
        self.driver3.setEnabled(False)
        self.clear1.setEnabled(False)
        self.clear2.setEnabled(False)
        self.clear3.setEnabled(False)

        if not self.session_select.isEnabled():
            self.session_select.setEnabled(True)

        self.grand_prix = self.grandprix_select.currentText()

        event = ff1.get_event(self.year, self.grand_prix)
        self.session_select.addItem(event['Session1'])

        # Checking if the session has occured yet, & adding to the combo box as required
        if (event.get_session_date(event['Session2'],utc= True).replace(tzinfo=timezone.utc) + timedelta(hours= 5)) < self.current_utc_time:
            self.session_select.addItem(event['Session2'])
        if (event.get_session_date(event['Session3'],utc= True).replace(tzinfo=timezone.utc) + timedelta(hours= 5)) < self.current_utc_time:
            self.session_select.addItem(event['Session3'])
        if (event.get_session_date(event['Session4'],utc= True).replace(tzinfo=timezone.utc) + timedelta(hours= 5)) < self.current_utc_time:
            self.session_select.addItem(event['Session4'])
        if (event.get_session_date(event['Session5'],utc= True).replace(tzinfo=timezone.utc) + timedelta(hours= 5)) < self.current_utc_time:
            self.session_select.addItem(event['Session5'])

    # Adding Drivers from the selected Session to combo box
    def drivers_select(self):
        self.clear_data()
        self.export_data.setEnabled(True)
        self.driver1.setEnabled(True)
        self.driver2.setEnabled(True)
        self.driver3.setEnabled(True)
        self.clear1.setEnabled(True)
        self.clear2.setEnabled(True)
        self.clear3.setEnabled(True)
        self.session_name = self.session_select.currentText()
        self.current_session = ff1.get_session(self.year, self.grand_prix, self.session_name)
        self.current_session.load()
        self.circuit_info = self.current_session.get_circuit_info()

        drivers = getattr(self.current_session, 'drivers')    

        # Adding Drivers list to Combo Box
        for driver in drivers:
            name = self.current_session.get_driver(driver)
            self.driver1.addItem(name['DriverNumber'].zfill(2) + ":  " + name['FullName'])
            self.driver2.addItem(name['DriverNumber'].zfill(2) + ":  " + name['FullName']) 
            self.driver3.addItem(name['DriverNumber'].zfill(2) + ":  " + name['FullName'])
    
    '''
    Updating the headshots for the selected driver
        id: index for which driver is being updated
    '''
    def update_headshot(self, id):   
        driver_headshot = QIcon('images/driver_headshots/' + str(self.year) + '/' + self.drivers[id] + '.webp')
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

                if getattr(self.current_session, 'name') == 'Qualifying' or getattr(self.current_session, 'name') == 'Sprint Qualifying' or getattr(self.current_session, 'name') == 'Sprint Shootout':
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

                if getattr(self.current_session, 'name') == 'Qualifying' or getattr(self.current_session, 'name') == 'Sprint Qualifying' or getattr(self.current_session, 'name') == 'Sprint Shootout':
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

                if self.session_name == 'Qualifying' or self.session_name == 'Sprint Qualifying' or self.session_name == 'Sprint Shootout':
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
            if self.session_name == 'Qualifying' or self.session_name == 'Sprint Qualifying' or self.session_name == 'Sprint Shootout':
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
            if self.session_name == 'Qualifying' or self.session_name == 'Sprint Qualifying' or self.session_name == 'Sprint Shootout':
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
            if self.session_name == 'Qualifying' or self.session_name == 'Sprint Qualifying' or self.session_name == 'Sprint Shootout':
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

        # Clearing driver data only if plotted prior
        if not self.speed_tel1[id] == '':
            self.clear_driver_data(id)

        event = ff1.get_event(self.year, self.grand_prix)

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
        self.plot_corner_points()
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
            if self.year == 2024:
                if self.session_name == 'Qualifying' or self.session_name == 'Sprint Qualifying' or self.session_name == 'Sprint Shootout':
                    driv_color = ff1.plotting.driver_color(driver_lap['Driver'])                    
                else:
                    driv_color = ff1.plotting.driver_color(driver_lap['Driver'].iat[0])               
            else:
                if self.session_name == 'Qualifying' or self.session_name == 'Sprint Qualifying' or self.session_name == 'Sprint Shootout':
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
            if self.session_name == 'Qualifying' or self.session_name == 'Sprint Qualifying' or self.session_name == 'Sprint Shootout':
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
            
            if self.session_name == 'Qualifying' or self.session_name == 'Sprint Qualifying' or self.session_name == 'Sprint Shootout':
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
    def plot_corner_points(self):
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
            if self.year == 2024:
                if self.session_name == 'Qualifying' or self.session_name == 'Sprint Qualifying' or self.session_name == 'Sprint Shootout':
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
                if self.session_name == 'Qualifying' or self.session_name == 'Sprint Qualifying' or self.session_name == 'Sprint Shootout':
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
                        if self.session_name == 'Qualifying' or self.session_name == 'Sprint Qualifying' or self.session_name == 'Sprint Shootout':
                            ref_name = ref_lap['Driver']
                        else:
                            ref_name = ref_lap['Driver'].iat[0]
                        driver_count = driver_count + 1
                        continue
                    
                    # Finding the delta time of the following laps with respect to the first
                    else:
                        driver_lap = self.driver_laps[id]
                        driver_tel = driver_lap.get_telemetry()

                        if self.year == 2024:
                            if self.session_name == 'Qualifying' or self.session_name == 'Sprint Qualifying' or self.session_name == 'Sprint Shootout':
                                driv_color = ff1.plotting.driver_color(driver_lap['Driver'])
                                driver_name = driver_lap['Driver']
                            else:
                                driv_color = ff1.plotting.driver_color(driver_lap['Driver'].iat[0])
                                driver_name = driver_lap['Driver'].iat[0]
                            
                        else:
                            if self.session_name == 'Qualifying' or self.session_name == 'Sprint Qualifying' or self.session_name == 'Sprint Shootout':
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
                if self.year == 2024:
                    if self.session_name == 'Qualifying' or self.session_name == 'Sprint Qualifying' or self.session_name == 'Sprint Shootout':
                        driv_color = ff1.plotting.driver_color(driver_lap['Driver'])
                    else:
                        driv_color = ff1.plotting.driver_color(driver_lap['Driver'].iat[0])

                        if int(driver_lap['LapNumber'].iloc[0]) == 1:
                            temp_lap = self.current_session.laps.pick_fastest()
                            temp_tel = temp_lap.get_telemetry().add_distance()
                            driver_tel['Distance'] = driver_tel['Distance'] + (temp_tel['Distance'].max() - driver_tel['Distance'].max())
                
                else:
                    if self.session_name == 'Qualifying' or self.session_name == 'Sprint Qualifying' or self.session_name == 'Sprint Shootout':
                        driv_color = ff1.plotting.team_color(driver_lap['Team'])
                    else:
                        driv_color = ff1.plotting.team_color(driver_lap['Team'].iat[0])

                        if int(driver_lap['LapNumber'].iloc[0]) == 1:
                            temp_lap = self.current_session.laps.pick_fastest()
                            temp_tel = temp_lap.get_telemetry().add_distance()
                            driver_tel['Distance'] = driver_tel['Distance'] + (temp_tel['Distance'].max() - driver_tel['Distance'].max())
                
                driver_tel['Driver'] = self.drivers[i]

                # Generating array of driver colors and driver numbers to be passed on to matplotlib for plotting
                if i == 0:
                    telemetry = driver_tel
                    driver_colors = [driv_color]
                    driver_numbers = [self.drivers[i]]
                else:
                    if driver_count == 0:
                        telemetry = driver_tel
                    else:
                        telemetry = telemetry._append(driver_tel)
                    driver_colors.append(driv_color)

                    if self.drivers[i] == driver_numbers[i-1]:
                        driver_numbers.append(self.drivers[i] + '.1')
                    elif self.drivers[i] == driver_numbers[i-2]:
                        driver_numbers.append(self.drivers[i] + '.2')
                    else:
                        driver_numbers.append(self.drivers[i])
                
                driver_count = driver_count + 1
            
            else:
                if i == 0:
                    driver_colors = ['white']
                    driver_numbers = ['0']
                else:
                    driver_colors.append('white')
                    driver_numbers.append('0')

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
                msector_dom = filtered_data.groupby(['Minisector', 'Driver'])['Speed'].mean().reset_index()

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
            fastest_driver = fastest_driver[['Minisector', 'Driver']].rename(columns={'Driver': 'Fastest_driver'})
            # Joining the fastest driver per minisector with the full telemetry
            telemetry = telemetry.merge(fastest_driver, on=['Minisector'])
            # Order the data by distance to ensure matplotlib plotting compatibility
            telemetry = telemetry.sort_values(by=['Distance'])

            # Plotting the data on the Track Domination widget
            self.track_dom_canvas.clear_visual()
            self.track_dom_canvas.plot_dom(telemetry, driver_numbers, driver_colors)
            self.track_dom_canvas.plot_corners(self.circuit_info)
            self.track_dom_canvas.can.draw()

    # Converting driver strings to only driver numbers
    def get_driver_no(self):
        self.drivers = [self.driver1.currentText(), self.driver2.currentText(), self.driver3.currentText()]
        for i, driver in enumerate(self.drivers):
            if self.drivers[i] == '':
                self.drivers[i] = '0'

            else:
                temp = re.findall(r'\b\d+\b', self.drivers[i])
                self.drivers[i] = temp[0].lstrip("0") 

    # Exporting Data
    def export(self):
        directory = 'exports/' + str(self.year) + '_' + self.grand_prix + '_' + self.session_name
        os.makedirs(directory, exist_ok=True)

        if self.session_results_exp.isChecked():
            self.current_session.results.to_csv(directory + '/session_results.csv')

        if self.circuit_info_exp.isChecked():
            self.circuit_info.corners.to_csv(directory + '/circuit_corners.csv')
            self.circuit_info.marshal_lights.to_csv(directory + '/circuit_marshal_lights.csv')
            self.circuit_info.marshal_sectors.to_csv(directory + '/circuit_marshal_sectors.csv')

            # Converting Track Rotation into a single element dataframe
            rotation = pd.DataFrame(columns= ['TrackRotation'])
            rotation.loc[0] = self.circuit_info.rotation
            rotation.to_csv(directory + '/circuit_rotation.csv')

        # Checking if a driver telemetry data has been loaded
        is_enabled1 = self.lap_sel1.isEnabled()
        is_enabled2 = self.lap_sel2.isEnabled()
        is_enabled3 = self.lap_sel3.isEnabled()
        is_enabled = (is_enabled1 or is_enabled2 or is_enabled3)

        if is_enabled:
            lap_directory = directory + '/driver_laps'
            os.makedirs(lap_directory, exist_ok=True)
            for i in range(len(self.drivers)):
                if self.laps[i] == '':
                    continue
                lap_data = self.driver_laps[i]
                driver_name = lap_data['Driver']
                lap_number = int(lap_data['LapNumber'])
                temp_lap = self.current_session.laps.pick_driver(self.drivers[i]).pick_wo_box().pick_fastest()
                weather = lap_data.get_weather_data()
                telemetry = lap_data.get_telemetry()

                if temp_lap['LapNumber'] == lap_number:
                    lap = str(lap_number) + '_personalBest'              
                else:
                    lap = str(lap_number)
                
                if self.lap_data_exp.isChecked():
                    lap_data.to_csv(lap_directory + '/'+ driver_name + '_'+ lap + '.csv')
                
                if self.weather_exp.isChecked():
                    weather.to_csv(lap_directory + '/'+ driver_name + '_'+ lap + '_weatherData.csv')
                
                if self.telemetry_data_exp.isChecked():
                    telemetry.to_csv(lap_directory + '/'+ driver_name + '_'+ lap + '_telemetry.csv')

# Checking for Internet connection for enablement of offline cache
def check_internet_connection():
    remote_server = "www.google.com"
    port = 80
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    try:
        sock.connect((remote_server, port))
        return True
    except socket.error:
        return False
    finally:
        sock.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Setting UI quality factors
    QtGui.QFontDatabase.addApplicationFont("/Users/niratpai/Library/Fonts/Formula1.ttf")
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "5"
    os.environ["QT_SCALE_FACTOR"] = '1.25'
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)

    # Loading App CSS & style
    qss="app_style.qss"
    with open(qss,"r") as fh:
        app.setStyleSheet(fh.read())
    app.setStyle('fusion')

    # Enabling offline cache while disconnected from the internet
    if check_internet_connection():
        print("Connection Status: ONLINE")
    else:
        print("Connection Status: OFFLINE")
        print("Enabling offline cache.....")
        ff1.Cache.offline_mode(True)

    window = ui()
    window.show()
    app.exec_()