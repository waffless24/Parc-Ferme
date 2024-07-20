''' ALL APP LIBRARY IMPORTS AND MODIFICATIONS'''
# PyQt5
from PyQt5.QtWidgets import QWidget
import PyQt5.uic as uic 

class UI_settings(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        uic.loadUi('settings_page.ui', self)