import sys
import os
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSpinBox, QDoubleSpinBox,
    QFileDialog, QTextEdit, QGroupBox, QFormLayout, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
import combine_data
from datetime import datetime

class ConversionWorker(QThread):
    """Worker thread for running the conversion process."""
    progress = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, args):
        super().__init__()
        self.args = args
        self._is_running = True
        self._original_print = print

    def stop(self):
        self._is_running = False

    def should_continue(self):
        return self._is_running

    def run(self):
        # Override print to capture output
        def custom_print(*args, **kwargs):
            if not self._is_running:
                return
            self.progress.emit(" ".join(map(str, args)))
        
        # Store original print function and replace it
        import builtins
        builtins.print = custom_print

        try:
            # Check if we should stop before starting
            if not self._is_running:
                return

            combine_data.process_measurements(self.args, callback=self.should_continue)
            
            # Only emit finished if we completed normally (not stopped)
            if self._is_running:
                self.finished.emit()

        except FileNotFoundError as e:
            self.error.emit(f"Error: File or directory not found - {str(e)}")
        except PermissionError as e:
            self.error.emit(f"Error: Permission denied - {str(e)}")
        except Exception as e:
            if self._is_running:  # Only emit error if we're not stopping
                self.error.emit(f"Error: An unexpected error occurred - {str(e)}")
        finally:
            # Restore original print function
            builtins.print = self._original_print

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Combine Soller Slit P02.2 Data")
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
        self.config_table.setHorizontalHeaderLabels(["N Images", "Name"])
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
        
        # Add clear button below log
        self.clear_button = QPushButton("🗑")  # Trash can icon
        self.clear_button.setToolTip("Clear log output")
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #666666;
                color: white;
                border: none;
                padding: 2px;
                font-size: 14px;
                min-width: 24px;
                min-height: 24px;
                max-width: 24px;
                max-height: 24px;
            }
            QPushButton:hover {
                background-color: #555555;
            }
        """)
        self.clear_button.clicked.connect(self.clear_log)
        
        # Create a layout for the clear button to align it to the right
        clear_layout = QHBoxLayout()
        clear_layout.addStretch()  # Push button to the right
        clear_layout.addWidget(self.clear_button)
        log_layout.addLayout(clear_layout)
        
        log_group.setLayout(log_layout)
        right_layout.addWidget(log_group)

        # Add right widget to main layout
        main_layout.addWidget(right_widget, stretch=1)  # Changed from 1 to 1

        # Connect browse buttons
        input_browse.clicked.connect(lambda: self.browse_directory(self.input_dir))
        output_browse.clicked.connect(lambda: self.browse_directory(self.output_dir))

        # Initialize worker
        self.worker = None

        # Load saved state
        self.load_state()

    def get_state_file_path(self):
        """Get the path to the state file."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, "combined_data_gui_state.json")

    def save_state(self):
        """Save the current state of the GUI to a file."""
        state = {
            "input_dir": self.input_dir.text(),
            "output_dir": self.output_dir.text(),
            "prefix": self.prefix.text(),
            "start_idx": self.start_idx.value(),
            "end_idx": self.end_idx.value(),
            "cosmic_sigma": self.cosmic_sigma.value(),
            "cosmic_window": self.cosmic_window.value(),
            "cosmic_iterations": self.cosmic_iterations.value(),
            "cosmic_min": self.cosmic_min.value(),
            "config_table": []
        }

        # Save configuration table
        for row in range(self.config_table.rowCount()):
            num_images = self.config_table.item(row, 0).text()
            name = self.config_table.item(row, 1).text()
            state["config_table"].append({
                "num_images": num_images,
                "name": name
            })

        try:
            with open(self.get_state_file_path(), 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            self.log(f"Error saving state: {str(e)}")

    def load_state(self):
        """Load the saved state of the GUI from a file."""
        try:
            with open(self.get_state_file_path(), 'r') as f:
                state = json.load(f)

            # Load basic settings
            self.input_dir.setText(state.get("input_dir", self.input_dir.text()))
            self.output_dir.setText(state.get("output_dir", self.output_dir.text()))
            self.prefix.setText(state.get("prefix", self.prefix.text()))
            self.start_idx.setValue(state.get("start_idx", self.start_idx.value()))
            self.end_idx.setValue(state.get("end_idx", self.end_idx.value()))
            self.cosmic_sigma.setValue(state.get("cosmic_sigma", self.cosmic_sigma.value()))
            self.cosmic_window.setValue(state.get("cosmic_window", self.cosmic_window.value()))
            self.cosmic_iterations.setValue(state.get("cosmic_iterations", self.cosmic_iterations.value()))
            self.cosmic_min.setValue(state.get("cosmic_min", self.cosmic_min.value()))

            # Load configuration table
            config_table = state.get("config_table", [])
            if config_table:
                self.config_table.setRowCount(len(config_table))
                for row, config in enumerate(config_table):
                    self.config_table.setItem(row, 0, QTableWidgetItem(str(config["num_images"])))
                    self.config_table.setItem(row, 1, QTableWidgetItem(config["name"]))

        except FileNotFoundError:
            # No saved state, use defaults
            pass
        except Exception as e:
            self.log(f"Error loading state: {str(e)}")

    def closeEvent(self, event):
        """Handle window close event."""
        self.save_state()
        super().closeEvent(event)

    def browse_directory(self, line_edit):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            line_edit.setText(directory)

    def log(self, message):
        """Add a message to the log output."""
        if message.startswith("Error:"):
            self.log_output.append(f'<span style="color: red;">{message}</span>')
        else:
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
                    self.log("Error: Name is required for row {row + 1}")
                    return
                config.append({"num_images": num_images, "name": name})
            except ValueError:
                self.log("Error: Invalid number of images in row {row + 1}")
                return

        # Create arguments object
        class Args:
            pass
        args = Args()
        args.input = self.input_dir.text()
        args.output = self.output_dir.text()
        args.start = self.start_idx.value()
        args.end = self.end_idx.value()
        args.prefix = self.prefix.text()
        args.cosmic_sigma = self.cosmic_sigma.value()
        args.cosmic_window = self.cosmic_window.value()
        args.cosmic_iterations = self.cosmic_iterations.value()
        args.cosmic_min = self.cosmic_min.value()
        args.config = json.dumps(config)

        # Clean up any existing worker
        if self.worker is not None:
            self.worker.stop()
            self.worker = None

        # Disable controls
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        # Add separator to log
        self.log_output.append("=" * 40)
        self.log_output.append('<span style="color: #CCCCCC; font-weight: bold;">▶ Starting new conversion process</span>')
        self.log_output.append(f'<span style="color: gray;">{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</span>')
        self.log_output.append("=" * 40)
        self.log_output.append("")

        # Start conversion
        self.worker = ConversionWorker(args)
        self.worker.progress.connect(self.log)
        self.worker.error.connect(self.handle_error)
        self.worker.finished.connect(self.conversion_finished)
        self.worker.start()

    def handle_error(self, error_message):
        """Handle error messages from the worker thread."""
        self.log(error_message)
        self.stop_conversion()

    def stop_conversion(self):
        if self.worker is not None:
            self.worker.stop()
            self.log_output.append("")  # Add empty line before stop message
            self.log_output.append("=" * 40)
            self.log_output.append('<span style="color: red; font-weight: bold;">■ Conversion stopped by user</span>')
            self.log_output.append(f'<span style="color: gray;">{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</span>')
            self.log_output.append("=" * 40)
            self.log_output.append("")  # Add empty line after stop message
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)

    def conversion_finished(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.log_output.append("")  # Add empty line before completion message
        self.log_output.append("=" * 40)
        self.log_output.append('<span style="color: green; font-weight: bold;">✓ Conversion completed successfully</span>')
        self.log_output.append(f'<span style="color: gray;">{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</span>')
        self.log_output.append("=" * 40)
        self.log_output.append("")  # Add empty line after completion message

    def clear_log(self):
        """Clear the log output."""
        self.log_output.clear()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 