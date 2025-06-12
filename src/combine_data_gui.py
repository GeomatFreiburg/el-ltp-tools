import sys
import os
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSpinBox, QDoubleSpinBox,
    QFileDialog, QTextEdit, QGroupBox, QFormLayout
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
        layout = QVBoxLayout(main_widget)

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
        layout.addWidget(io_group)

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
        layout.addWidget(file_group)

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
        layout.addWidget(cosmic_group)

        # Configuration section
        config_group = QGroupBox("Measurement Configuration")
        config_layout = QVBoxLayout()
        
        self.config_edit = QTextEdit()
        self.config_edit.setPlaceholderText(
            'Enter JSON configuration, e.g.:\n'
            '[\n'
            '  {"num_images": 2, "name": "center"},\n'
            '  {"num_images": 2, "name": "side"}\n'
            ']'
        )
        # Set default configuration
        default_config = [
            {"num_images": 2, "name": "center"},
            {"num_images": 2, "name": "side"}
        ]
        self.config_edit.setText(json.dumps(default_config, indent=2))
        self.config_edit.setMaximumHeight(100)
        config_layout.addWidget(self.config_edit)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Output log
        log_group = QGroupBox("Output Log")
        log_layout = QVBoxLayout()
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        log_layout.addWidget(self.log_output)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        # Control buttons
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start Conversion")
        self.start_button.clicked.connect(self.start_conversion)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_conversion)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        layout.addLayout(button_layout)

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

    def start_conversion(self):
        # Validate inputs
        if not self.input_dir.text() or not self.output_dir.text():
            self.log("Error: Please select input and output directories")
            return

        try:
            config = json.loads(self.config_edit.toPlainText())
        except json.JSONDecodeError as e:
            self.log(f"Error: Invalid JSON configuration: {e}")
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