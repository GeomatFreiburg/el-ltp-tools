import sys
import os
import json
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QDoubleSpinBox,
    QFileDialog,
    QTextEdit,
    QGroupBox,
    QFormLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)
from PyQt6.QtCore import QThread, pyqtSignal
from . import process_measurements
from datetime import datetime


class ConversionWorker(QThread):
    """Worker thread for running the conversion process.
    
    This class handles the background processing of image combination tasks,
    including cosmic ray detection and removal. It provides progress updates
    and error handling through Qt signals.
    
    Signals
    -------
    progress : pyqtSignal(str)
        Emitted with progress messages during processing.
    finished : pyqtSignal()
        Emitted when processing completes successfully.
    error : pyqtSignal(str)
        Emitted when an error occurs during processing.
    """

    progress = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, input_directory, output_directory, config, start_index, end_index,
                 cosmic_sigma, cosmic_window, cosmic_iterations, cosmic_min, prefix):
        """Initialize the worker thread.
        
        Parameters
        ----------
        input_directory : str
            Path to the directory containing input images.
        output_directory : str
            Path where combined images will be saved.
        config : str
            JSON string containing the configuration for directory groups.
        start_index : int
            Starting index for processing directories.
        end_index : int
            Ending index for processing directories.
        cosmic_sigma : float
            Sigma value for cosmic ray detection.
        cosmic_window : int
            Window size for cosmic ray detection.
        cosmic_iterations : int
            Number of iterations for cosmic ray detection.
        cosmic_min : float
            Minimum intensity threshold for cosmic ray detection.
        prefix : str
            Prefix for output filenames.
        """
        super().__init__()
        self.input_directory = input_directory
        self.output_directory = output_directory
        self.config = config
        self.start_index = start_index
        self.end_index = end_index
        self.cosmic_sigma = cosmic_sigma
        self.cosmic_window = cosmic_window
        self.cosmic_iterations = cosmic_iterations
        self.cosmic_min = cosmic_min
        self.prefix = prefix
        self._is_running = True
        self._original_print = print

    def stop(self):
        """Stop the processing thread."""
        self._is_running = False

    def should_continue(self):
        """Check if processing should continue.
        
        Returns
        -------
        bool
            True if processing should continue, False if it should stop.
        """
        return self._is_running

    def run(self):
        """Run the image combination process.
        
        This method:
        1. Sets up custom print function to capture output
        2. Processes the images using process_measurements
        3. Handles errors and emits appropriate signals
        4. Restores the original print function
        """
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

            process_measurements(
                input_directory=self.input_directory,
                output_directory=self.output_directory,
                config=self.config,
                start_index=self.start_index,
                end_index=self.end_index,
                cosmic_sigma=self.cosmic_sigma,
                cosmic_window=self.cosmic_window,
                cosmic_iterations=self.cosmic_iterations,
                cosmic_min=self.cosmic_min,
                prefix=self.prefix,
                callback=self.should_continue
            )

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
    """Main window for the image combination application.
    
    This class provides a graphical user interface for combining images
    with cosmic ray detection and removal. It includes settings for:
    - Input/output directories
    - File naming and indexing
    - Cosmic ray detection parameters
    - Measurement configuration
    """

    def __init__(self):
        """Initialize the main window and its components."""
        super().__init__()
        self.setWindowTitle("Combine Soller Slit P02.2 Data")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)

        # Initialize last used directory
        self.last_directory = os.path.expanduser("~")

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

        # Measurement configuration section
        config_group = QGroupBox("Measurement Configuration")
        config_layout = QVBoxLayout()

        # Table for configuration
        self.config_table = QTableWidget()
        self.config_table.setColumnCount(2)
        self.config_table.setHorizontalHeaderLabels(["Measurement Name", "Number of Directories"])
        self.config_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        config_layout.addWidget(self.config_table)

        # Buttons for adding/removing rows
        config_buttons = QHBoxLayout()
        add_row = QPushButton("Add Measurement")
        remove_row = QPushButton("Remove Measurement")
        config_buttons.addWidget(add_row)
        config_buttons.addWidget(remove_row)
        config_layout.addLayout(config_buttons)

        config_group.setLayout(config_layout)
        left_layout.addWidget(config_group)

        # Connect signals
        input_browse.clicked.connect(lambda: self.browse_directory(self.input_dir))
        output_browse.clicked.connect(lambda: self.browse_directory(self.output_dir))
        add_row.clicked.connect(self.add_config_row)
        remove_row.clicked.connect(self.remove_config_row)

        # Add default configuration rows
        self.add_config_row()
        self.add_config_row()
        self.config_table.setItem(0, 0, QTableWidgetItem("center"))
        self.config_table.setItem(0, 1, QTableWidgetItem("2"))
        self.config_table.setItem(1, 0, QTableWidgetItem("side"))
        self.config_table.setItem(1, 1, QTableWidgetItem("2"))

        # Add left widget to main layout
        main_layout.addWidget(left_widget, stretch=1)  # Changed from 2 to 1

        # Right side container for log and buttons
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Control buttons
        button_layout = QHBoxLayout()

        self.start_button = QPushButton("Start Conversion")
        self.start_button.setStyleSheet(
            """
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
        """
        )
        self.start_button.clicked.connect(self.start_conversion)
        button_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.setStyleSheet(
            """
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
        """
        )
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
        self.clear_button.setStyleSheet(
            """
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
        """
        )
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

        # Initialize worker
        self.worker = None

        # Load saved state
        self.load_state()

    def get_state_file_path(self):
        """Get the path to the state file.
        
        Returns
        -------
        str
            Path to the state file in the user's home directory.
        """
        # Get user's home directory
        home_dir = os.path.expanduser("~")
        config_dir = os.path.join(home_dir, ".el_ltp_tools")
        
        # Ensure config directory exists
        os.makedirs(config_dir, exist_ok=True)
        
        return os.path.join(config_dir, "combined_data_gui_state.json")

    def get_config_json(self):
        """Get the configuration as a JSON string.
        
        Returns
        -------
        str
            JSON string containing the configuration.
        """
        config = {}
        for row in range(self.config_table.rowCount()):
            name_item = self.config_table.item(row, 0)
            num_dirs_item = self.config_table.item(row, 1)
            if name_item and num_dirs_item:
                try:
                    num_dirs = int(num_dirs_item.text())
                    config[name_item.text()] = num_dirs
                except ValueError:
                    pass
        return json.dumps([config])

    def save_state(self):
        """Save the current state of the application."""
        state = {
            "input_directory": self.input_dir.text(),
            "output_directory": self.output_dir.text(),
            "prefix": self.prefix.text(),
            "start_index": self.start_idx.value(),
            "end_index": self.end_idx.value(),
            "cosmic_sigma": self.cosmic_sigma.value(),
            "cosmic_window": self.cosmic_window.value(),
            "cosmic_iterations": self.cosmic_iterations.value(),
            "cosmic_min": self.cosmic_min.value(),
            "config": self.get_config_json()
        }
        
        with open(self.get_state_file_path(), "w") as f:
            json.dump(state, f)

    def load_state(self):
        """Load the saved state of the application."""
        try:
            with open(self.get_state_file_path(), "r") as f:
                state = json.load(f)
                
            self.input_dir.setText(state.get("input_directory", ""))
            self.output_dir.setText(state.get("output_directory", ""))
            self.prefix.setText(state.get("prefix", ""))
            self.start_idx.setValue(state.get("start_index", 2))
            self.end_idx.setValue(state.get("end_index", 97))
            self.cosmic_sigma.setValue(state.get("cosmic_sigma", 6.0))
            self.cosmic_window.setValue(state.get("cosmic_window", 10))
            self.cosmic_iterations.setValue(state.get("cosmic_iterations", 3))
            self.cosmic_min.setValue(state.get("cosmic_min", 50.0))
            
            # Load configuration
            config = json.loads(state.get("config", '[{"center": 2, "side": 2}]'))[0]
            self.config_table.setRowCount(0)  # Clear existing rows
            for name, num_dirs in config.items():
                self.add_config_row()
                row = self.config_table.rowCount() - 1
                self.config_table.setItem(row, 0, QTableWidgetItem(name))
                self.config_table.setItem(row, 1, QTableWidgetItem(str(num_dirs)))
                
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def closeEvent(self, event):
        """Handle window close event.
        
        Parameters
        ----------
        event : QCloseEvent
            The close event.
        """
        self.save_state()
        super().closeEvent(event)

    def browse_directory(self, line_edit):
        """Open a directory browser dialog.
        
        Parameters
        ----------
        line_edit : QLineEdit
            The line edit widget to update with the selected directory.
        """
        directory = QFileDialog.getExistingDirectory(
            self, 
            "Select Directory",
            self.last_directory
        )
        if directory:
            line_edit.setText(directory)
            self.last_directory = directory  # Update last used directory

    def log(self, message):
        """Add a message to the log.
        
        Parameters
        ----------
        message : str
            The message to add to the log.
        """
        if message.startswith("Error:"):
            self.log_output.append(f'<span style="color: red;">{message}</span>')
        else:
            self.log_output.append(message)

    def add_config_row(self):
        """Add a new row to the configuration table."""
        current_row = self.config_table.rowCount()
        self.config_table.insertRow(current_row)
        self.config_table.setItem(current_row, 0, QTableWidgetItem(""))
        self.config_table.setItem(current_row, 1, QTableWidgetItem("2"))

    def remove_config_row(self):
        """Remove the last row from the configuration table."""
        current_row = self.config_table.currentRow()
        if current_row >= 0:
            self.config_table.removeRow(current_row)

    def start_conversion(self):
        """Start the image combination process."""
        # Get configuration from table
        config = {}
        for row in range(self.config_table.rowCount()):
            name_item = self.config_table.item(row, 0)
            num_dirs_item = self.config_table.item(row, 1)
            if name_item and num_dirs_item:
                try:
                    name = name_item.text()
                    num_dirs = int(num_dirs_item.text())
                    config[name] = num_dirs
                except ValueError:
                    self.handle_error(f"Invalid number of directories in row {row + 1}")
                    return

        if not config:
            self.handle_error("No valid configuration found")
            return

        # Create worker
        self.worker = ConversionWorker(
            input_directory=self.input_dir.text(),
            output_directory=self.output_dir.text(),
            config=json.dumps([config]),
            start_index=self.start_idx.value(),
            end_index=self.end_idx.value(),
            cosmic_sigma=self.cosmic_sigma.value(),
            cosmic_window=self.cosmic_window.value(),
            cosmic_iterations=self.cosmic_iterations.value(),
            cosmic_min=self.cosmic_min.value(),
            prefix=self.prefix.text()
        )

        # Connect signals
        self.worker.progress.connect(self.log)
        self.worker.error.connect(self.handle_error)
        self.worker.finished.connect(self.conversion_finished)

        # Start processing
        self.worker.start()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def handle_error(self, error_message):
        """Handle an error message.
        
        Parameters
        ----------
        error_message : str
            The error message to display.
        """
        self.log(error_message)
        self.stop_conversion()

    def stop_conversion(self):
        """Stop the current conversion process."""
        if self.worker is not None:
            self.worker.stop()
            self.log_output.append("")  # Add empty line before stop message
            self.log_output.append("=" * 40)
            self.log_output.append(
                '<span style="color: red; font-weight: bold;">■ Conversion stopped by user</span>'
            )
            self.log_output.append(
                f'<span style="color: gray;">{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</span>'
            )
            self.log_output.append("=" * 40)
            self.log_output.append("")  # Add empty line after stop message
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)

    def conversion_finished(self):
        """Handle completion of the conversion process."""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.log_output.append("")  # Add empty line before completion message
        self.log_output.append("=" * 40)
        self.log_output.append(
            '<span style="color: green; font-weight: bold;">✓ Conversion completed successfully</span>'
        )
        self.log_output.append(
            f'<span style="color: gray;">{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</span>'
        )
        self.log_output.append("=" * 40)
        self.log_output.append("")  # Add empty line after completion message

    def clear_log(self):
        """Clear the log display."""
        self.log_output.clear()


def main():
    """Main entry point for the application.
    
    This function:
    1. Creates the QApplication
    2. Creates and shows the main window
    3. Starts the event loop
    """
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
