import datetime
import json
from PySide2 import QtGui
from PySide2.QtGui import QPainter, QBrush, QColor, QPen
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox,
    QFileDialog, QWidget, QMessageBox, QTabWidget, QGroupBox, QTextEdit, QStyleFactory
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QRect
import cv2
import numpy as np


class ProgramInterfaceGUI(QMainWindow):
    def __init__(self, config_file='config.json', update_callback=None):
        super().__init__()
        self.config_file = config_file
        self.config = {}
        self.update_callback = update_callback
        self.default_config = {
            "DISCORD_WEBHOOK": "",
            "quadrado_bar": [238, 495, 380, 30],
            "barra_quadrado_bar": [238, 503, 324, 13],
            "quadrado_bar_progresso": [310, 531, 178, 4],
            "shake_area": [150, 50, 550, 450],
            "catch_delay": 2,
            "max_repeating_duration": 30,
            "tolerance": 5,
            "max_hold_time": 2.0,
            "min_hold_time": 0.1,
            "target_fish_x": 450,
            "target_hold_time": 3,
            "left_bound_x": 350
        }
        self.input_fields = {}
        self.drag_position = None  # For moving the window
        self.init_ui()
        try:
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
            self.sync_input_fields()
        except FileNotFoundError:
            self.config = self.default_config
            self.save_config()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load configuration: {e}")

    def init_ui(self):

        #self.setWindowFlags(Qt.WindowTitleHint)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("""
                           
        QMainWindow {
            background-color: transparent;
        }

        #title_bar{
            background-color: #23272a;
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;                   
        }
        #main_container {
            background-color: #3f3f3f;
            border-radius: 10px; /* Arredondamento das bordas */
        }       
        * {
            font-family: "Segoe UI Variable Small", serif;                   
        }
        QWidget {
            color: #9da5ae;
            font-size: 11px;
            background: #121212;
            font-weight: 250;
        }

        QTabWidget {
            background: #1e151c;    
        }
                           
        QGridLayout {
            background: #3f3f3f; 
            border-radius: 2px; 
            padding: 2px;
        }
                           
        QLabel {
             background: transparent;
             color: #8b8b8b;            
        }
        QTextEdit {
            background: #2b2c2d;
            border-radius: 2px;
        }
                        
                           
        QGroupBox {
            font-size: 15px;
            color: #fefefe;
            font-weight: 500;
        }
        """)

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAutoFillBackground(True)



        self.setGeometry(100, 100, 800, 500)
        QApplication.setStyle('Fusion')
        # Main layout

        self.main_layout = QVBoxLayout()
        #self.main_layout.setEnabled(True)
        #self.main_layout.setContentsMargins(0, -1, 0, 0)
        self.main_layout.setObjectName("main_layout")
        self.main_layout.setContentsMargins(0, 0, 0, 0)  

        #layout.setContentsMargins(5, 5, 5, 5)
        #self.setSpacing(0)

        # title bar
        self.title_bar = QWidget()
        self.title_bar.setFixedHeight(30)
        self.title_bar.setObjectName("title_bar")

        title_bar_layout = QHBoxLayout(self.title_bar)
        title_bar_layout.setContentsMargins(10, 0, 10, 0)
        #title_bar_layout.setSpacing(5)

        # title text
        self.title_label = QLabel("Fisch - Config Editor")
        self.title_label.setStyleSheet("color: white; font-size: 14px;")
        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.minimize_button = QPushButton("-")
        self.minimize_button.setFixedSize(20, 20)
        self.minimize_button.setStyleSheet("background-color: #7289da; color: white; border: none;")
        self.minimize_button.clicked.connect(self.showMinimized)

        self.maximize_button = QPushButton("□")
        self.maximize_button.setFixedSize(20, 20)
        self.maximize_button.setStyleSheet("background-color: #7289da; color: white; border: none;")
        self.maximize_button.clicked.connect(self.toggle_maximize_restore)

        self.close_button = QPushButton("X")
        self.close_button.setFixedSize(20, 20)
        self.close_button.setStyleSheet("background-color: #f04747; color: white; border: none;")
        self.close_button.clicked.connect(self.close)

        #  widgets to title bar layout
        title_bar_layout.addWidget(self.title_label)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(self.minimize_button)
        title_bar_layout.addWidget(self.maximize_button)
        title_bar_layout.addWidget(self.close_button)

        #  title bar to main layout
        self.main_layout.addWidget(self.title_bar)

        #font = QtGui.QFont()
        #font.setFamily("Segoe UI Variable Small")
        #font.setPointSize(-1)
        #font.setBold(False)
        #font.setWeight(50)
        #self.setFont(font)

        # Tabs
        self.tabs = QTabWidget()

        self.tabs.setStyleSheet("""
                    QTabWidget::pane {
                        border: 1px solid #202225;
                        border-bottom-left-radius: 15px;
                        border-bottom-right-radius: 15px;
                    }
                    QTabBar::tab {
                        background: #2c2f33;
                        color: white;
                        padding: 5px;
                        border: 1px solid #202225;
                    }
                    QTabBar::tab:selected {
                        background: #5865f2;
                    }
        """)

        # general Tab
        self.tab_general = QWidget()
        general_layout = QVBoxLayout()

        # general Info GroupBox
        general_group = QGroupBox("General Info")
        general_info_layout = QGridLayout()

        self.caught_general_label = QLabel(f"Fish Caught: 0")
        self.lost_general_label = QLabel("Fish Lost: 0")

        self.is_catching_general_label = QLabel("Is catching: False")
        self.is_navigation_general_label = QLabel("Is UI Navigation Active: False")
        self.is_repeating_general_label = QLabel("Is Repeating Keys [s, enter]: False")
        self.started_general_label = QLabel("Started: False")
        self.fps_general_label = QLabel("[This Program] FPS: 60")
        self.rod_bar_general_label = QLabel("Rod Bar: False")
        self.fish_column_general_label = QLabel("Fish Column: False")
        self.progress_bar_general_label = QLabel("Progress Bar: False")
        
        
        general_info_layout.addWidget(self.caught_general_label, 0, 0, Qt.AlignmentFlag.AlignLeft)
        general_info_layout.addWidget(self.lost_general_label, 1, 0, Qt.AlignmentFlag.AlignLeft)
        general_info_layout.addWidget(self.is_catching_general_label, 2, 0, Qt.AlignmentFlag.AlignLeft)
        general_info_layout.addWidget(self.is_navigation_general_label, 3, 0, Qt.AlignmentFlag.AlignLeft)
        general_info_layout.addWidget(self.is_repeating_general_label, 4, 0, Qt.AlignmentFlag.AlignLeft)
        general_info_layout.addWidget(self.started_general_label, 5, 0, Qt.AlignmentFlag.AlignLeft)
        general_info_layout.addWidget(self.fps_general_label, 6, 0, Qt.AlignmentFlag.AlignLeft)
        general_info_layout.addWidget(self.rod_bar_general_label, 7, 0, Qt.AlignmentFlag.AlignLeft)
        general_info_layout.addWidget(self.fish_column_general_label, 8, 0, Qt.AlignmentFlag.AlignLeft)
        general_info_layout.addWidget(self.progress_bar_general_label, 9, 0, Qt.AlignmentFlag.AlignLeft)

        general_group.setLayout(general_info_layout)
        general_layout.addWidget(general_group)

        # Style Dropdown GroupBox
        #style_group = QGroupBox("Style Selector")
        #style_layout = QVBoxLayout()

        #self.style_dropdown = QComboBox()
        #self.style_dropdown.addItems(QStyleFactory.keys())  
        #self.style_dropdown.currentTextChanged.connect(self.change_style)

        #style_layout.addWidget(QLabel("Select Style:"))
        #style_layout.addWidget(self.style_dropdown)

        #style_group.setLayout(style_layout)
        #general_layout.addWidget(style_group)

        logs_group = QGroupBox("Logs")
        logs_layout = QVBoxLayout()
        self.logs_text_edit = QTextEdit()
        self.logs_text_edit.setReadOnly(True)
        logs_layout.addWidget(self.logs_text_edit)
        logs_group.setLayout(logs_layout)

        general_layout.addWidget(logs_group)
        self.tab_general.setLayout(general_layout)

        self.tabs.addTab(self.tab_general, "General")

        self.tab_variables = QWidget()
        variables_layout = QVBoxLayout()

        variables_group = QGroupBox("Variables")
        grid_layout = QGridLayout()

        for row, (key, value) in enumerate(self.default_config.items()):
            label = QLabel(f"{key}:")
            if isinstance(value, list):  # List field
                line_edit = QLineEdit(str(value))
                line_edit.editingFinished.connect(lambda key=key, field=line_edit: self.update_variable(key, field.text(), is_list=True))
                grid_layout.addWidget(label, row, 0)
                grid_layout.addWidget(line_edit, row, 1)
                self.input_fields[key] = line_edit
            elif isinstance(value, (int, float)): 
                if isinstance(value, int):
                    spin_box = QSpinBox()
                    spin_box.setMaximum(99999)
                    spin_box.setValue(value)
                    spin_box.valueChanged.connect(lambda val, key=key: self.update_variable(key, val))
                    grid_layout.addWidget(label, row, 0)
                    grid_layout.addWidget(spin_box, row, 1)
                    self.input_fields[key] = spin_box
                else:
                    double_spin_box = QDoubleSpinBox()
                    double_spin_box.setDecimals(2)
                    double_spin_box.setMaximum(99999)
                    double_spin_box.setValue(value)
                    double_spin_box.valueChanged.connect(lambda val, key=key: self.update_variable(key, val))
                    grid_layout.addWidget(label, row, 0)
                    grid_layout.addWidget(double_spin_box, row, 1)
                    self.input_fields[key] = double_spin_box
            elif isinstance(value, str):  # String field
                line_edit = QLineEdit(value)
                line_edit.editingFinished.connect(lambda key=key, field=line_edit: self.update_variable(key, field.text()))
                grid_layout.addWidget(label, row, 0)
                grid_layout.addWidget(line_edit, row, 1)
                self.input_fields[key] = line_edit

        variables_group.setLayout(grid_layout)
        variables_layout.addWidget(variables_group)

        config_buttons = QHBoxLayout()
        load_button = QPushButton("Load Config")
        load_button.clicked.connect(self.load_config)
        save_button = QPushButton("Save Config")
        save_button.clicked.connect(self.save_config)
        config_buttons.addWidget(load_button)
        config_buttons.addWidget(save_button)

        variables_layout.addLayout(config_buttons)

        self.tab_variables.setLayout(variables_layout)
        self.tabs.addTab(self.tab_variables, "Variables")

        self.tab_roi = QWidget()
        roiLayout = QVBoxLayout(self.tab_roi)

        self.roi_label = QLabel("No ROI yet")
        self.roi_label.setAlignment(Qt.AlignCenter)
        roiLayout.addWidget(self.roi_label)

        self.tab_roi.setLayout(roiLayout)
        self.tabs.addTab(self.tab_roi, "ROI")

        self.main_layout.addWidget(self.tabs)

        container = QWidget()
        container.setObjectName("main_container")
        container.setLayout(self.main_layout)
        self.setCentralWidget(container)

    def change_style(self, style_name):
        """Change the application style."""
        QApplication.setStyle(style_name)

    def toggle_maximize_restore(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_position:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def add_log_entry(self, message):
        """Append a log entry to the logs text edit."""
        self.logs_text_edit.append(f"[{datetime.datetime.now()}] - {message}")

    def update_variable(self, key, value, is_list=False):
        try:
            if is_list:
                self.config[key] = json.loads(value)
            else:
                self.config[key] = type(self.default_config[key])(value)
            if self.update_callback:
                self.update_callback(self.config)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Invalid value for {key}: {e}")

    def load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
            self.sync_input_fields()
        except FileNotFoundError:
            self.config = self.default_config
            self.save_config()

    def save_config(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {e}")

    def sync_input_fields(self):
        for key, field in self.input_fields.items():
            if isinstance(field, QLineEdit):
                field.setText(str(self.config.get(key, self.default_config[key])))
            elif isinstance(field, QSpinBox):
                field.setValue(self.config.get(key, self.default_config[key]))
            elif isinstance(field, QDoubleSpinBox):
                field.setValue(self.config.get(key, self.default_config[key]))
    
    def update_roi(self, frame):
        """Update the ROI display in the GUI."""
        if frame is None:
            return
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        qt_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        self.roi_label.setPixmap(pixmap)
        self.roi_label.setAlignment(Qt.AlignCenter)