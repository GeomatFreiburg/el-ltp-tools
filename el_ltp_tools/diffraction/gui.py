import sys
import os
import json
import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')  # Set the backend to Qt before importing pyplot
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QTextEdit,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLabel,
    QStyledItemDelegate,
    QDialog,
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QPainter, QFontMetrics
from .script import integrate_multi
from datetime import datetime


class RightAlignElideLeftDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = (
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

    def paint(self, painter: QPainter, option, index):
        # Customize elided text
        painter.save()

        text = index.data(Qt.ItemDataRole.DisplayRole)
        if text is None:
            text = ""

        # Get the rect for the text
        text_rect = option.rect
        text_rect.setRight(text_rect.right() - 4)  # Add some padding

        # Prepare font metrics and elide from left
        font_metrics = QFontMetrics(option.font)
        elided = font_metrics.elidedText(
            text, Qt.TextElideMode.ElideLeft, text_rect.width()
        )

        # Draw the text
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            elided,
        )

        painter.restore()


class IntegrationWorker(QThread):
    """Worker thread for running the integration process."""

    progress = pyqtSignal(str)
    finished = pyqtSignal(list)  # Changed to emit the integrated patterns
    error = pyqtSignal(str)

    def __init__(self, input_dir, output_dir, file_configs):
        super().__init__()
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.file_configs = file_configs
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

            # Create output directory if it doesn't exist
            os.makedirs(self.output_dir, exist_ok=True)

            # Run integration
            integrated_patterns = integrate_multi(
                self.input_dir, self.output_dir, self.file_configs
            )

            # Only emit finished if we completed normally (not stopped)
            if self._is_running:
                self.finished.emit(integrated_patterns)

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
        self.setWindowTitle("EL-LTP Tools - Multi-Detector Integration")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)

        # Initialize last used directories
        self.last_directory = os.path.expanduser("~")
        self.last_calibration_dir = os.path.expanduser("~")
        self.last_mask_dir = os.path.expanduser("~")

        # Get the directory where the script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(script_dir, "../.."))

        # Set default paths
        default_input_dir = os.path.join(project_root, "Data/BX90_13_empty_2_combined")
        default_output_dir = os.path.join(
            project_root, "Data/BX90_13_empty_2_integrated"
        )

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)  # Changed to vertical layout

        # Input/Output section
        io_group = QGroupBox("Input/Output Settings")
        io_layout = QVBoxLayout()

        # Input directory
        input_label = QLabel("Input Directory:")
        self.input_dir = QLineEdit(default_input_dir)
        input_browse = QPushButton("Browse...")
        input_browse.setToolTip("Select directory containing the input diffraction images")
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_dir)
        input_layout.addWidget(input_browse)
        io_layout.addWidget(input_label)
        io_layout.addLayout(input_layout)

        # Output directory
        output_label = QLabel("Output Directory:")
        self.output_dir = QLineEdit(default_output_dir)
        output_browse = QPushButton("Browse...")
        output_browse.setToolTip("Select directory where integrated patterns will be saved")
        output_layout = QHBoxLayout()
        output_layout.addWidget(self.output_dir)
        output_layout.addWidget(output_browse)
        io_layout.addWidget(output_label)
        io_layout.addLayout(output_layout)

        io_group.setLayout(io_layout)
        main_layout.addWidget(io_group)

        # Detector Configuration section
        config_group = QGroupBox("Detector Configuration")
        config_layout = QVBoxLayout()

        # Create table widget
        self.config_table = QTableWidget()
        self.config_table.setColumnCount(5)
        self.config_table.setHorizontalHeaderLabels(
            ["Name", "Calibration File", "", "Mask File", ""]
        )

        # Then set resize modes
        self.config_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.config_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.config_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self.config_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch
        )
        self.config_table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.ResizeToContents
        )

        # Set empty header labels for button columns
        self.config_table.horizontalHeaderItem(2).setText("")
        self.config_table.horizontalHeaderItem(4).setText("")

        self.config_table.setMinimumHeight(200)

        # Apply custom delegate to file path columns
        delegate = RightAlignElideLeftDelegate()
        self.config_table.setItemDelegateForColumn(
            1, delegate
        )  # Calibration file column
        self.config_table.setItemDelegateForColumn(3, delegate)  # Mask file column

        # Add default rows
        self.config_table.setRowCount(2)
        default_calibration = "Hello LONG LONG LONG LONG TEXT where is this world?"
        default_mask = ""
        for i in range(2):
            name_item = QTableWidgetItem("center" if i == 0 else "side")
            cal_item = QTableWidgetItem(default_calibration)
            mask_item = QTableWidgetItem(default_mask)

            # Create browse buttons
            cal_browse = QPushButton("...")
            cal_browse.setFixedWidth(45)
            cal_browse.setStyleSheet("padding: 0px; margin: 0px;")
            cal_browse.setToolTip("Select calibration file (.poni) for this detector position")
            cal_browse.clicked.connect(
                lambda checked, row=i: self.browse_file(row, "calibration")
            )

            mask_browse = QPushButton("...")
            mask_browse.setFixedWidth(45)
            mask_browse.setStyleSheet("padding: 0px; margin: 0px;")
            mask_browse.setToolTip("Select mask file (.mask) for this detector position")
            mask_browse.clicked.connect(
                lambda checked, row=i: self.browse_file(row, "mask")
            )

            self.config_table.setItem(i, 0, name_item)
            self.config_table.setItem(i, 1, cal_item)
            self.config_table.setCellWidget(i, 2, cal_browse)
            self.config_table.setItem(i, 3, mask_item)
            self.config_table.setCellWidget(i, 4, mask_browse)

        # Connect cell changed signal
        self.config_table.cellChanged.connect(self.handle_cell_changed)

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
        main_layout.addWidget(config_group)

        # Control buttons
        button_layout = QHBoxLayout()

        self.start_button = QPushButton("Start Integration")
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
        self.start_button.clicked.connect(self.start_integration)
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
        self.stop_button.clicked.connect(self.stop_integration)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)

        main_layout.addLayout(button_layout)

        # Output log
        log_group = QGroupBox("Output Log")
        log_layout = QVBoxLayout()

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(200)  # Limit the height of the log
        log_layout.addWidget(self.log_output)

        # Add clear button below log
        self.clear_button = QPushButton("🗑")
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
        clear_layout.addStretch()
        clear_layout.addWidget(self.clear_button)
        log_layout.addLayout(clear_layout)

        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)

        # Connect browse buttons
        input_browse.clicked.connect(lambda: self.browse_directory(self.input_dir, "Select Input Directory"))
        output_browse.clicked.connect(lambda: self.browse_directory(self.output_dir, "Select Output Directory"))

        # Initialize worker
        self.worker = None

        # Load saved state
        self.load_state()

    def get_state_file_path(self):
        """Get the path to the state file."""
        home_dir = os.path.expanduser("~")
        config_dir = os.path.join(home_dir, ".el_ltp_tools")
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, "diffraction_gui_state.json")

    def save_state(self):
        """Save the current state of the GUI to a file."""
        state = {
            "input_dir": self.input_dir.text(),
            "output_dir": self.output_dir.text(),
            "config_table": [],
            "last_directory": self.last_directory,
            "last_calibration_dir": self.last_calibration_dir,
            "last_mask_dir": self.last_mask_dir,
        }

        # Save configuration table
        for row in range(self.config_table.rowCount()):
            name = self.config_table.item(row, 0).text()
            calibration = self.config_table.item(row, 1).text()
            mask = self.config_table.item(row, 3).text()
            state["config_table"].append(
                {"name": name, "calibration": calibration, "mask": mask}
            )

        try:
            with open(self.get_state_file_path(), "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            self.log(f"Error saving state: {str(e)}")

    def load_state(self):
        """Load the saved state of the GUI from a file."""
        try:
            with open(self.get_state_file_path(), "r") as f:
                state = json.load(f)

            # Load basic settings
            self.input_dir.setText(state.get("input_dir", self.input_dir.text()))
            self.output_dir.setText(state.get("output_dir", self.output_dir.text()))
            self.last_directory = state.get("last_directory", os.path.expanduser("~"))
            self.last_calibration_dir = state.get(
                "last_calibration_dir", os.path.expanduser("~")
            )
            self.last_mask_dir = state.get("last_mask_dir", os.path.expanduser("~"))

            # Load configuration table
            config_table = state.get("config_table", [])
            if config_table:
                self.config_table.setRowCount(len(config_table))
                for row, config in enumerate(config_table):
                    self.config_table.setItem(row, 0, QTableWidgetItem(config["name"]))

                    cal_item = QTableWidgetItem(config["calibration"])
                    cal_item.setTextAlignment(
                        int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    )
                    self.config_table.setItem(row, 1, cal_item)

                    mask_item = QTableWidgetItem(config["mask"])
                    mask_item.setTextAlignment(
                        int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    )
                    self.config_table.setItem(row, 3, mask_item)

        except FileNotFoundError:
            # No saved state, use defaults
            pass
        except Exception as e:
            self.log(f"Error loading state: {str(e)}")

    def closeEvent(self, event):
        """Handle window close event."""
        self.save_state()
        super().closeEvent(event)

    def browse_directory(self, line_edit, title):
        """Open file dialog to select a directory.
        
        Args:
            line_edit: The QLineEdit widget to update with the selected directory
            title: The window title for the file dialog
        """
        directory = QFileDialog.getExistingDirectory(
            self, title, self.last_directory
        )
        if directory:
            line_edit.setText(directory)
            self.last_directory = directory

    def log(self, message):
        """Add a message to the log output."""
        if message.startswith("Error:"):
            self.log_output.append(f'<span style="color: red;">{message}</span>')
        else:
            self.log_output.append(message)
            # Add a blank line after "saved integrated pattern" messages
            if "saved integrated pattern" in message:
                self.log_output.append("")

    def handle_cell_changed(self, row, column):
        """Handle cell changes in the configuration table."""
        if column in [1, 3]:  # Calibration or Mask file columns
            item = self.config_table.item(row, column)
            if item:
                # Set tooltip to show full path
                item.setToolTip(item.text())

    def add_config_row(self):
        current_row = self.config_table.rowCount()
        self.config_table.insertRow(current_row)
        self.config_table.setItem(current_row, 0, QTableWidgetItem(""))

        # Create items
        cal_item = QTableWidgetItem("")
        mask_item = QTableWidgetItem("")

        # Create browse buttons
        cal_browse = QPushButton("...")
        cal_browse.setFixedWidth(45)
        cal_browse.setStyleSheet("padding: 0px; margin: 0px;")
        cal_browse.setToolTip("Select calibration file (.poni) for this detector position")
        cal_browse.clicked.connect(
            lambda checked, row=current_row: self.browse_file(row, "calibration")
        )

        mask_browse = QPushButton("...")
        mask_browse.setFixedWidth(45)
        mask_browse.setStyleSheet("padding: 0px; margin: 0px;")
        mask_browse.setToolTip("Select mask file (.mask) for this detector position")
        mask_browse.clicked.connect(
            lambda checked, row=current_row: self.browse_file(row, "mask")
        )

        self.config_table.setItem(current_row, 1, cal_item)
        self.config_table.setCellWidget(current_row, 2, cal_browse)
        self.config_table.setItem(current_row, 3, mask_item)
        self.config_table.setCellWidget(current_row, 4, mask_browse)

        # Set alignment after setting items
        cal_item.setTextAlignment(
            int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        )
        mask_item.setTextAlignment(
            int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        )

    def remove_config_row(self):
        current_row = self.config_table.currentRow()
        if current_row >= 0:
            self.config_table.removeRow(current_row)

    def browse_file(self, row, file_type):
        """Open file dialog to select calibration or mask file."""
        if file_type == "calibration":
            file_filter = "Calibration Files (*.poni);;All Files (*)"
            current_file = self.config_table.item(row, 1).text()
            start_dir = (
                os.path.abspath(os.path.dirname(current_file))
                if current_file
                else self.last_calibration_dir
            )
        else:  # mask
            file_filter = "Mask Files (*.mask);;All Files (*)"
            current_file = self.config_table.item(row, 3).text()
            start_dir = (
                os.path.abspath(os.path.dirname(current_file))
                if current_file
                else self.last_mask_dir
            )

        # Create and configure the file dialog
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setWindowTitle(f"Select {file_type} file")
        dialog.setNameFilter(file_filter)
        dialog.setDirectory(start_dir)

        if dialog.exec():
            file_paths = dialog.selectedFiles()
            if file_paths:
                file_path = file_paths[0]  # Get the first selected file

                # Update the file path in the table
                if file_type == "calibration":
                    item = self.config_table.item(row, 1)
                    item.setText(file_path)
                    item.setTextAlignment(
                        int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    )
                    self.last_calibration_dir = os.path.dirname(file_path)
                else:
                    item = self.config_table.item(row, 3)
                    item.setText(file_path)
                    item.setTextAlignment(
                        int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    )
                    self.last_mask_dir = os.path.dirname(file_path)

    def get_config_table_data(self):
        """Get the full configuration data from the table."""
        file_configs = {}
        for row in range(self.config_table.rowCount()):
            name = self.config_table.item(row, 0).text()
            calibration = self.config_table.item(row, 1).text()
            mask = self.config_table.item(row, 3).text()  # Updated column index

            if not name or not calibration or not mask:
                continue

            file_configs[name] = {"calibration": calibration, "mask": mask}
        return file_configs

    def start_integration(self):
        # Validate inputs
        if not self.input_dir.text() or not self.output_dir.text():
            self.log("Error: Please select input and output directories")
            return

        # Get configuration from table
        file_configs = self.get_config_table_data()
        if not file_configs:
            self.log("Error: Please configure at least one detector")
            return

        # Clean up any existing worker
        if self.worker is not None:
            self.worker.stop()
            self.worker = None

        # Disable controls
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        # Add separator to log
        self.log_output.append("=" * 40)
        self.log_output.append(
            '<span style="color: #CCCCCC; font-weight: bold;">▶ Starting new integration process</span>'
        )
        self.log_output.append(
            f'<span style="color: gray;">{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</span>'
        )
        self.log_output.append("=" * 40)
        self.log_output.append("")

        # Start integration
        self.worker = IntegrationWorker(
            self.input_dir.text(), self.output_dir.text(), file_configs
        )
        self.worker.progress.connect(self.log)
        self.worker.error.connect(self.handle_error)
        self.worker.finished.connect(self.integration_finished)
        self.worker.start()

    def handle_error(self, error_message):
        """Handle error messages from the worker thread."""
        self.log(error_message)
        self.stop_integration()

    def stop_integration(self):
        if self.worker is not None:
            self.worker.stop()
            self.log_output.append("")
            self.log_output.append("=" * 40)
            self.log_output.append(
                '<span style="color: red; font-weight: bold;">■ Integration stopped by user</span>'
            )
            self.log_output.append(
                f'<span style="color: gray;">{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</span>'
            )
            self.log_output.append("=" * 40)
            self.log_output.append("")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)

    def integration_finished(self, integrated_patterns):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.log_output.append("")
        self.log_output.append("=" * 40)
        self.log_output.append(
            '<span style="color: green; font-weight: bold;">✓ Integration completed successfully</span>'
        )
        self.log_output.append(
            f'<span style="color: gray;">{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</span>'
        )
        self.log_output.append("=" * 40)
        self.log_output.append("")

        # Plot the integrated patterns
        try:
            # Create a new dialog window for the plot
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            plot_dialog = QDialog(self)
            plot_dialog.setWindowTitle(f"EL-LTP Tools - Integrated Diffraction Patterns - {current_time}")
            plot_dialog.resize(1200, 800)
            plot_dialog.setWindowFlags(plot_dialog.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
            
            # Create layout for the dialog
            layout = QVBoxLayout(plot_dialog)
            
            # Create figure and canvas
            fig = Figure(figsize=(12, 8))
            canvas = FigureCanvas(fig)
            
            # Add navigation toolbar
            toolbar = NavigationToolbar(canvas, plot_dialog)
            layout.addWidget(toolbar)
            layout.addWidget(canvas)
            
            # Create the plot
            ax = fig.add_subplot(111)
            
            # Calculate the offset for vertical spacing
            # Get the maximum intensity across all patterns
            max_intensity = max(max(I) for _, I in integrated_patterns)
            min_intensity = min(min(I) for _, I in integrated_patterns)
            spacing_offset = (max_intensity - min_intensity) * 0.05  # 5% of data range as spacing
            
            for i, (q, I) in enumerate(integrated_patterns):
                # Add an offset to the intensity that increases with each pattern
                offset_I = I + (i * spacing_offset)
                ax.plot(q, offset_I, label=f"Pattern {i+1:04d}")

            ax.set_xlabel("q (Å⁻¹)")
            ax.set_ylabel("Intensity (a.u.)")
            ax.set_title("Integrated Diffraction Patterns")
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            fig.tight_layout()
            
            # Show the dialog non-modally
            plot_dialog.show()

        except Exception as e:
            self.log(f"Error plotting patterns: {str(e)}")

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
