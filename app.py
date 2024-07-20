''' ALL APP LIBRARY IMPORTS AND MODIFICATIONS'''
# PyQt5
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QButtonGroup, QShortcut, QStyledItemDelegate
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

# Plotting Libraries
import pyqtgraph as pg
from matplotlib import font_manager
import matplotlib.pyplot as plt

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
import pandas as pd

# Setting Cache Directory
ff1.Cache.enable_cache('cache')

# UI pages
from driver_comparison import UI_driver
from settings import UI_settings

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
 
class ui(QMainWindow):
    def __init__(self):
        super().__init__()

        loadUi('main_window.ui', self)

        # Stylizing the QComboBoxes with the applied QSS in .ui file
        self.grandprix_select.setItemDelegate(QStyledItemDelegate(self.grandprix_select))
        self.session_select.setItemDelegate(QStyledItemDelegate(self.session_select))

        self.stackedWidget.addWidget(QWidget())
        self.stackedWidget.addWidget(QWidget())
        self.driver_comparison = UI_driver()
        self.stackedWidget.addWidget(self.driver_comparison)
        self.stackedWidget.addWidget(QWidget())
        self.settings_page = UI_settings()
        self.stackedWidget.addWidget(self.settings_page)

        self.stackedWidget.setCurrentIndex(2)

        self.setWindowTitle('F1 Data Analysis')

        # TASK BAR MODIFICATIONS
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
        
        # Populating Current Grand-Prix Selection ComboBox
        self.weekend_enable()

        # Year Selection
        self.year_select.valueChanged.connect(self.weekend_enable)
        # Race Selection
        self.grandprix_select.currentIndexChanged.connect(self.session_enable)
        # Session Selection
        self.session_select.currentIndexChanged.connect(self.load)

        # Exporting Data
        self.export_data.clicked.connect(self.export)

    def switch_tabs(self):
        id = self.tabs.checkedId()
        self.stackedWidget.setCurrentIndex(id)  
    
        # Filling the combo box with the list of Grand-Prix's of the selected Season
    def weekend_enable(self):
        self.export_data.setEnabled(False)
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
        self.export_data.setEnabled(False)

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

    def load(self):
        if self.session_select.currentIndex() == -1:
            self.driver_comparison.disable_drivers()
            return
        
        self.export_data.setEnabled(True)
        self.session_name = self.session_select.currentText()
        self.current_session = ff1.get_session(self.year, self.grand_prix, self.session_name)
        self.current_session.load()
        self.circuit_info = self.current_session.get_circuit_info()

        self.driver_comparison.receive_parameters(self.current_session, self.circuit_info)

    # Exporting Data
    def export(self):
        directory = 'exports/' + str(self.year) + '_' + self.grand_prix + '_' + self.session_name
        os.makedirs(directory, exist_ok=True)

        if self.session_results_exp.isChecked():
            self.driver_comparison.current_session.results.to_csv(directory + '/session_results.csv')

        if self.circuit_info_exp.isChecked():
            self.driver_comparison.circuit_info.corners.to_csv(directory + '/circuit_corners.csv')
            self.driver_comparison.circuit_info.marshal_lights.to_csv(directory + '/circuit_marshal_lights.csv')
            self.driver_comparison.circuit_info.marshal_sectors.to_csv(directory + '/circuit_marshal_sectors.csv')

            # Converting Track Rotation into a single element dataframe
            rotation = pd.DataFrame(columns= ['TrackRotation'])
            rotation.loc[0] = self.driver_comparison.circuit_info.rotation
            rotation.to_csv(directory + '/circuit_rotation.csv')

        # Checking if a driver telemetry data has been loaded
        is_enabled1 = self.driver_comparison.lap_sel1.isEnabled()
        is_enabled2 = self.driver_comparison.lap_sel2.isEnabled()
        is_enabled3 = self.driver_comparison.lap_sel3.isEnabled()
        is_enabled = (is_enabled1 or is_enabled2 or is_enabled3)

        if is_enabled:
            lap_directory = directory + '/driver_laps'
            os.makedirs(lap_directory, exist_ok=True)
            for i in range(len(self.driver_comparison.drivers)):
                if self.driver_comparison.laps[i] == '':
                    continue
                lap_data = self.driver_comparison.driver_laps[i]
                driver_name = lap_data['Driver']
                lap_number = int(lap_data['LapNumber'])
                temp_lap = self.driver_comparison.current_session.laps.pick_driver(self.drivers[i]).pick_wo_box().pick_fastest()
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