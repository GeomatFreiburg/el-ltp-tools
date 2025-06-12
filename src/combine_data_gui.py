import sys
import os
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSpinBox, QDoubleSpinBox,
    QFileDialog, QTextEdit, QGroupBox, QFormLayout, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import combine_data

class ConversionWorker(QThread):
    """Worker thread for running the conversion process."""
    progress = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, args):
        super().__init__()
        self.args = args

    def run(self):
        # Override print to capture output
        def custom_print(*args, **kwargs):
            self.progress.emit(" ".join(map(str, args)))
        
        # Store original print function
        original_print = print
        # Replace print with our custom version
        import builtins
        builtins.print = custom_print

        try:
            combine_data.process_measurements(self.args)
        finally:
            # Restore original print function
            builtins.print = original_print
            self.finished.emit()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data Conversion Tool")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)

        # Get the directory where the script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(script_dir, "../.."))
        
        # Set default paths
        default_input_dir = os.path.join(project_root, "Data/CaSiO3_2")
        default_output_dir = os.path.join(project_root, "Data/CaSiO3_2_combined")

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)  # Changed to horizontal layout

        # Left side container for all settings
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Input/Output section
        io_group = QGroupBox("Input/Output Settings")
        io_layout = QFormLayout()
        
        # Input directory
        self.input_dir = QLineEdit(default_input_dir)
        input_browse = QPushButton("Browse...")
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_dir)
        input_layout.addWidget(input_browse)
        io_layout.addRow("Input Directory:", input_layout)
        
        # Output directory
        self.output_dir = QLineEdit(default_output_dir)
        output_browse = QPushButton("Browse...")
        output_layout = QHBoxLayout()
        output_layout.addWidget(self.output_dir)
        output_layout.addWidget(output_browse)
        io_layout.addRow("Output Directory:", output_layout)
        
        io_group.setLayout(io_layout)
        left_layout.addWidget(io_group)

        # File settings section
        file_group = QGroupBox("File Settings")
        file_layout = QFormLayout()
        
        self.base_filename = QLineEdit("CaSiO3_")
        file_layout.addRow("Base Filename:", self.base_filename)
        
        self.prefix = QLineEdit("CaSiO3_2")
        file_layout.addRow("Output Prefix:", self.prefix)
        
        self.start_idx = QSpinBox()
        self.start_idx.setRange(1, 999)
        self.start_idx.setValue(2)
        file_layout.addRow("Start Index:", self.start_idx)
        
        self.end_idx = QSpinBox()
        self.end_idx.setRange(1, 999)
        self.end_idx.setValue(97)
        file_layout.addRow("End Index:", self.end_idx)
        
        file_group.setLayout(file_layout)
        left_layout.addWidget(file_group)

        # Cosmic ray detection section
        cosmic_group = QGroupBox("Cosmic Ray Detection")
        cosmic_layout = QFormLayout()
        
        self.cosmic_sigma = QDoubleSpinBox()
        self.cosmic_sigma.setRange(1.0, 20.0)
        self.cosmic_sigma.setValue(6.0)
        self.cosmic_sigma.setSingleStep(0.5)
        cosmic_layout.addRow("Sigma:", self.cosmic_sigma)
        
        self.cosmic_window = QSpinBox()
        self.cosmic_window.setRange(3, 21)
        self.cosmic_window.setValue(10)
        self.cosmic_window.setSingleStep(2)
        cosmic_layout.addRow("Window Size:", self.cosmic_window)
        
        self.cosmic_iterations = QSpinBox()
        self.cosmic_iterations.setRange(1, 10)
        self.cosmic_iterations.setValue(3)
        cosmic_layout.addRow("Iterations:", self.cosmic_iterations)
        
        self.cosmic_min = QDoubleSpinBox()
        self.cosmic_min.setRange(0.0, 1000.0)
        self.cosmic_min.setValue(50.0)
        self.cosmic_min.setSingleStep(10.0)
        cosmic_layout.addRow("Minimum Intensity:", self.cosmic_min)
        
        cosmic_group.setLayout(cosmic_layout)
        left_layout.addWidget(cosmic_group)

        # Configuration section
        config_group = QGroupBox("Measurement Configuration")
        config_layout = QVBoxLayout()
        
        # Create table widget
        self.config_table = QTableWidget()
        self.config_table.setColumnCount(2)
        self.config_table.setHorizontalHeaderLabels(["Number of Images", "Name"])
        self.config_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.config_table.setMinimumHeight(200)  # Set minimum height for the table
        
        # Add default rows
        self.config_table.setRowCount(2)
        for i in range(2):
            num_images_item = QTableWidgetItem("2")
            name_item = QTableWidgetItem("center" if i == 0 else "side")
            self.config_table.setItem(i, 0, num_images_item)
            self.config_table.setItem(i, 1, name_item)
        
        # Add/Remove row buttons
        button_layout = QHBoxLayout()
        add_row_btn = QPushButton("Add Row")
        remove_row_btn = QPushButton("Remove Row")
        add_row_btn.clicked.connect(self.add_config_row)
        remove_row_btn.clicked.connect(self.remove_config_row)
        button_layout.addWidget(add_row_btn)
        button_layout.addWidget(remove_row_btn)
        
        config_layout.addWidget(self.config_table)
        config_layout.addLayout(button_layout)
        
        config_group.setLayout(config_layout)
        left_layout.addWidget(config_group)

        # Add left widget to main layout
        main_layout.addWidget(left_widget, stretch=1)  # Changed from 2 to 1

        # Right side container for log and buttons
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Control buttons
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start Conversion")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 15px;
                font-size: 14px;
                font-weight: bold;
                min-height: 50px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.start_button.clicked.connect(self.start_conversion)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 15px;
                font-size: 14px;
                font-weight: bold;
                min-height: 50px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.stop_button.clicked.connect(self.stop_conversion)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        right_layout.addLayout(button_layout)

        # Output log
        log_group = QGroupBox("Output Log")
        log_layout = QVBoxLayout()
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        log_layout.addWidget(self.log_output)
        
        log_group.setLayout(log_layout)
        right_layout.addWidget(log_group)

        # Add right widget to main layout
        main_layout.addWidget(right_widget, stretch=1)  # Changed from 1 to 1

        # Connect browse buttons
        input_browse.clicked.connect(lambda: self.browse_directory(self.input_dir))
        output_browse.clicked.connect(lambda: self.browse_directory(self.output_dir))

        # Initialize worker
        self.worker = None

    def browse_directory(self, line_edit):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            line_edit.setText(directory)

    def log(self, message):
        self.log_output.append(message)

    def add_config_row(self):
        current_row = self.config_table.rowCount()
        self.config_table.insertRow(current_row)
        self.config_table.setItem(current_row, 0, QTableWidgetItem("2"))
        self.config_table.setItem(current_row, 1, QTableWidgetItem(""))

    def remove_config_row(self):
        current_row = self.config_table.currentRow()
        if current_row >= 0:
            self.config_table.removeRow(current_row)

    def start_conversion(self):
        # Validate inputs
        if not self.input_dir.text() or not self.output_dir.text():
            self.log("Error: Please select input and output directories")
            return

        # Get configuration from table
        config = []
        for row in range(self.config_table.rowCount()):
            try:
                num_images = int(self.config_table.item(row, 0).text())
                name = self.config_table.item(row, 1).text()
                if not name:
                    self.log(f"Error: Name is required for row {row + 1}")
                    return
                config.append({"num_images": num_images, "name": name})
            except ValueError:
                self.log(f"Error: Invalid number of images in row {row + 1}")
                return

        # Create arguments object
        class Args:
            pass
        args = Args()
        args.input = self.input_dir.text()
        args.output = self.output_dir.text()
        args.start = self.start_idx.value()
        args.end = self.end_idx.value()
        args.base_filename = self.base_filename.text()
        args.prefix = self.prefix.text()
        args.cosmic_sigma = self.cosmic_sigma.value()
        args.cosmic_window = self.cosmic_window.value()
        args.cosmic_iterations = self.cosmic_iterations.value()
        args.cosmic_min = self.cosmic_min.value()
        args.config = json.dumps(config)

        # Disable controls
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        # Start conversion
        self.worker = ConversionWorker(args)
        self.worker.progress.connect(self.log)
        self.worker.finished.connect(self.conversion_finished)
        self.worker.start()

    def stop_conversion(self):
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
            self.log("Conversion stopped by user")
            self.conversion_finished()

    def conversion_finished(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.log("Conversion finished")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 