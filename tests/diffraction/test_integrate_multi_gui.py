import os
import tempfile
import shutil
import pytest
from PyQt6.QtWidgets import QApplication, QFileDialog
from PyQt6.QtCore import Qt, QEventLoop, QTimer
from el_ltp_tools.diffraction.integrate_multi_gui import MainWindow, IntegrationWorker
import numpy as np
import fabio.tifimage
from PIL import Image
import glob


@pytest.fixture(scope="session")
def app():
    """Create a QApplication instance."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    app.quit()


@pytest.fixture
def temp_dir():
    """Create a temporary directory with test files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_config_files(temp_dir):
    """Create mock configuration files for testing."""
    poni_path = os.path.join(temp_dir, "test.poni")
    mask_path = os.path.join(temp_dir, "test.mask")
    
    # Create .poni file
    poni_content = """# Nota: C-Order, 1 refers to the Y axis, 2 to the X axis
# Calibration done at Tue Oct 15 22:20:08 2024
poni_version: 2
Detector: Detector
Detector_config: {"pixel1": 1.0e-4, "pixel2": 1.0e-4, "max_shape": [100, 100]}
Distance: 1.0
Poni1: 0.0
Poni2: 0.0
Rot1: 0.0
Rot2: 0.0
Rot3: 0.0
Wavelength: 1.0e-10
"""
    with open(poni_path, 'w') as f:
        f.write(poni_content)
    
    # Create mask file
    mask_data = np.zeros((100, 100), dtype=np.float32)
    Image.fromarray(mask_data).save(mask_path, format='TIFF')
    
    return {"poni": poni_path, "mask": mask_path}


@pytest.fixture
def test_files(temp_dir):
    """Create test input files for both center and side configurations."""
    input_dir = os.path.join(temp_dir, "input")
    os.makedirs(input_dir, exist_ok=True)
    
    # Create test image data
    test_data = np.zeros((100, 100), dtype=np.float32)
    test_data[50, 50] = 1.0  # Add a peak in the center
    
    # Save test files using fabio
    for i in range(1, 4):
        fabio.tifimage.tifimage(data=test_data).write(os.path.join(input_dir, f"test_center_{i}.tif"))
        fabio.tifimage.tifimage(data=test_data).write(os.path.join(input_dir, f"test_side_{i}.tif"))
    
    return input_dir


@pytest.fixture
def configured_window(app, temp_dir, mock_config_files, test_files):
    """Create a MainWindow with configured detector settings."""
    window = MainWindow()
    
    # Set up input/output directories
    output_dir = os.path.join(temp_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    window.input_dir.setText(test_files)  # Use the input dir from test_files fixture
    window.output_dir.setText(output_dir)
    
    # Set up configuration
    window.config_table.item(0, 0).setText("center")  # Set the name
    window.config_table.item(0, 1).setText(mock_config_files["poni"])
    window.config_table.item(0, 3).setText(mock_config_files["mask"])
    window.config_table.item(1, 0).setText("side")  # Set the name
    window.config_table.item(1, 1).setText(mock_config_files["poni"])
    window.config_table.item(1, 3).setText(mock_config_files["mask"])
    
    return window


def test_main_window_initialization(app):
    """Test that the main window initializes correctly."""
    window = MainWindow()
    window.show()  # Make sure the window is shown
    app.processEvents()  # Process any pending events
    
    assert window.windowTitle() == "EL-LTP Tools - Multi-Detector Integration"
    assert window.config_table.rowCount() == 2  # Default rows
    assert window.config_table.columnCount() == 5  # Name, Calibration, Browse, Mask, Browse
    
    window.close()  # Clean up
    app.processEvents()  # Process any pending events


def test_config_table_default_values(app):
    """Test that the configuration table has correct default values."""
    window = MainWindow()
    # Check first row (center)
    assert window.config_table.item(0, 0).text() == "center"
    # Check second row (side)
    assert window.config_table.item(1, 0).text() == "side"


def test_add_config_row(app):
    """Test adding a new configuration row."""
    window = MainWindow()
    initial_rows = window.config_table.rowCount()
    window.add_config_row()
    assert window.config_table.rowCount() == initial_rows + 1
    # Check that the new row has empty values
    new_row = initial_rows
    assert window.config_table.item(new_row, 0).text() == ""
    assert window.config_table.item(new_row, 1).text() == ""
    assert window.config_table.item(new_row, 3).text() == ""


def test_remove_config_row(app):
    """Test removing a configuration row."""
    window = MainWindow()
    # Add a row first
    window.add_config_row()
    initial_rows = window.config_table.rowCount()
    # Select the last row
    window.config_table.selectRow(initial_rows - 1)
    # Remove the selected row
    window.remove_config_row()
    assert window.config_table.rowCount() == initial_rows - 1


def test_browse_directory(app, temp_dir, monkeypatch):
    """Test directory browsing functionality."""
    window = MainWindow()
    
    def mock_get_directory(*args, **kwargs):
        return temp_dir
    
    # Patch QFileDialog.getExistingDirectory
    monkeypatch.setattr(QFileDialog, 'getExistingDirectory', mock_get_directory)
    
    # Call the browse function
    window.browse_directory(window.input_dir, "Test Directory")
    assert window.input_dir.text() == temp_dir


def test_browse_file(app, temp_dir, mock_config_files, monkeypatch):
    """Test file browsing functionality."""
    window = MainWindow()
    
    # Add a row to the configuration table
    window.add_config_row()
    
    def mock_get_open_file_name(parent, title, start_dir, filter):
        if "poni" in filter:
            return mock_config_files["poni"], filter
        return mock_config_files["mask"], filter
    
    # Mock QFileDialog.getOpenFileName
    monkeypatch.setattr(QFileDialog, "getOpenFileName", mock_get_open_file_name)
    
    # Test browsing for calibration file
    window.browse_file(0, "calibration")
    assert window.config_table.item(0, 1).text() == mock_config_files["poni"]
    
    # Test browsing for mask file
    window.browse_file(0, "mask")
    assert window.config_table.item(0, 3).text() == mock_config_files["mask"]


def test_get_config_table_data(app, mock_config_files):
    """Test getting configuration data from the table."""
    window = MainWindow()
    # Set up the table with our mock files
    window.config_table.item(0, 1).setText(mock_config_files["poni"])
    window.config_table.item(0, 3).setText(mock_config_files["mask"])
    window.config_table.item(1, 1).setText(mock_config_files["poni"])
    window.config_table.item(1, 3).setText(mock_config_files["mask"])

    config_data = window.get_config_table_data()
    assert len(config_data) == 2
    assert "center" in config_data
    assert "side" in config_data
    assert config_data["center"]["calibration"] == mock_config_files["poni"]
    assert config_data["center"]["mask"] == mock_config_files["mask"]
    assert config_data["side"]["calibration"] == mock_config_files["poni"]
    assert config_data["side"]["mask"] == mock_config_files["mask"]


def wait_for_worker(worker, app, timeout=5000):
    """Helper function to wait for a worker to complete with timeout."""
    # Wait for worker to be created
    while worker is None:
        app.processEvents()
    
    # Create event loop and wait for worker to finish
    loop = QEventLoop()
    worker.finished.connect(loop.quit)
    worker.error.connect(loop.quit)
    
    # Set up timer for timeout
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(loop.quit)
    timer.start(timeout)
    
    # Start event loop
    loop.exec()
    
    # Check if we timed out
    if timer.isActive():
        timer.stop()
        return True
    else:
        print("Worker did not complete within timeout")
        worker.terminate()
        worker.wait()
        return False


def check_output_files(output_dir, expected_count=3):
    """Helper function to check output files."""
    output_files = sorted(glob.glob(os.path.join(output_dir, "*.xy")))
    assert len(output_files) == expected_count, f"Expected {expected_count} output files, got {len(output_files)}"
    for output_file in output_files:
        data = np.loadtxt(output_file)
        assert data.shape[1] == 2, f"Expected 2 columns in {output_file}, got {data.shape[1]}"
        assert data.shape[0] > 0, f"Expected non-empty data in {output_file}"
    return output_files


@pytest.fixture
def worker_setup(app, temp_dir, mock_config_files, test_files):
    """Setup for worker tests with common configuration."""
    output_dir = os.path.join(temp_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    
    config = {
        "center": {
            "calibration": mock_config_files["poni"],
            "mask": mock_config_files["mask"]
        },
        "side": {
            "calibration": mock_config_files["poni"],
            "mask": mock_config_files["mask"]
        }
    }
    
    return {
        "input_dir": test_files,
        "output_dir": output_dir,
        "config": config
    }


def test_integration_worker(app, worker_setup):
    """Test the integration worker thread."""
    # Create worker
    worker = IntegrationWorker(
        worker_setup["input_dir"],
        worker_setup["output_dir"],
        worker_setup["config"]
    )
    
    # Test error signal
    error_messages = []
    def on_error(msg):
        error_messages.append(msg)
    worker.error.connect(on_error)
    
    # Test finished signal
    finished_patterns = []
    def on_finished(patterns):
        finished_patterns.extend(patterns)
    worker.finished.connect(on_finished)
    
    # Start worker and wait for completion
    worker.start()
    assert wait_for_worker(worker, app), "Worker timed out"
    
    # Check for errors
    assert len(error_messages) == 0, f"Errors occurred: {error_messages}"
    
    # Check that patterns were returned
    assert len(finished_patterns) == 3, f"Expected 3 patterns, got {len(finished_patterns)}"
    
    # Check output files
    check_output_files(worker_setup["output_dir"])


def test_integration_worker_stop(app, worker_setup):
    """Test stopping the integration worker."""
    # Create worker
    worker = IntegrationWorker(
        worker_setup["input_dir"],
        worker_setup["output_dir"],
        worker_setup["config"]
    )
    
    # Test error signal
    error_messages = []
    def on_error(msg):
        error_messages.append(msg)
    worker.error.connect(on_error)
    
    # Test finished signal
    finished_patterns = []
    def on_finished(patterns):
        finished_patterns.extend(patterns)
    worker.finished.connect(on_finished)
    
    # Start worker
    worker.start()
    
    # Wait a bit longer for worker to start and process some data
    QTimer.singleShot(500, worker.stop)
    
    # Wait for completion
    assert wait_for_worker(worker, app), "Worker timed out"
    
    # Check for errors
    assert len(error_messages) == 0, f"Errors occurred: {error_messages}"
    
    # Clean up
    worker.deleteLater()
    app.processEvents()


def test_main_window_integration(app, configured_window, test_files):
    """Test the integration functionality in MainWindow."""
    # Start integration
    configured_window.start_integration()
    
    # Wait for worker to complete
    assert wait_for_worker(configured_window.worker, app), "Worker timed out"
    
    # Check for errors in log
    log_text = configured_window.log_output.toPlainText()
    assert "Error:" not in log_text, f"Errors occurred: {log_text}"
    
    # Check output files
    check_output_files(configured_window.output_dir.text())


def test_main_window_plotting(app, temp_dir):
    """Test the plotting functionality in MainWindow."""
    window = MainWindow()
    
    # Create test patterns
    patterns = []
    for i in range(3):
        q = np.linspace(0, 10, 100)
        I = np.sin(q) + i
        patterns.append((q, I))
    
    # Test plotting
    window.integration_finished(patterns)
    
    # Check that the log doesn't contain any error messages
    log_text = window.log_output.toPlainText()
    assert "Error plotting patterns" not in log_text 