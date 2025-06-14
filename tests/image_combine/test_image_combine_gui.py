import os
import json
import pytest
import numpy as np
from PIL import Image
from PyQt6.QtWidgets import QApplication, QFileDialog, QPushButton, QTableWidgetItem
from PyQt6.QtCore import Qt
from el_ltp_tools.image_combine.gui import MainWindow
from unittest.mock import patch


def create_test_data(tmp_path):
    """Create test data for the image combine tests."""
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    
    # Create test directories
    for i in range(1, 4):
        dir_path = input_dir / f"g{i}"
        dir_path.mkdir()
        
        # Create test images in each directory
        for j in range(3):
            img_data = np.zeros((100, 100), dtype=np.float32)
            img_data[50, 50] = 1.0  # Add a peak in the center
            img = Image.fromarray(img_data)
            img.save(dir_path / f"test_{j}.tif")


@pytest.fixture
def mock_state_file(tmp_path):
    """Create a temporary state file for testing."""
    state_file = tmp_path / "test_state.json"
    with patch('el_ltp_tools.image_combine.gui.MainWindow.get_state_file_path') as mock_get_path:
        mock_get_path.return_value = str(state_file)
        yield state_file


@pytest.fixture
def main_window(qtbot, tmp_path, mock_state_file):
    """Create a MainWindow instance with temporary directories."""
    window = MainWindow()
    qtbot.addWidget(window)
    
    # Create test data
    create_test_data(tmp_path)
    
    # Set up temporary directories
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # Set the input and output directories
    window.input_dir.setText(str(input_dir))
    window.output_dir.setText(str(output_dir))
    
    # Reset all values to defaults
    window.prefix.setText("CaSiO3_2")
    window.start_idx.setValue(1)
    window.end_idx.setValue(3)
    window.cosmic_sigma.setValue(6.0)
    window.cosmic_window.setValue(10)
    window.cosmic_iterations.setValue(3)
    window.cosmic_min.setValue(50.0)
    
    # Set up default configuration
    window.config_table.setItem(0, 0, QTableWidgetItem("center"))
    window.config_table.setItem(0, 1, QTableWidgetItem("2"))
    window.config_table.setItem(1, 0, QTableWidgetItem("side"))
    window.config_table.setItem(1, 1, QTableWidgetItem("2"))
    
    return window


def test_window_initialization(main_window):
    """Test that the window initializes correctly."""
    assert main_window.windowTitle() == "Combine Soller Slit P02.2 Data"
    assert main_window.input_dir.text() != ""
    assert main_window.output_dir.text() != ""
    assert main_window.prefix.text() == "CaSiO3_2"
    assert main_window.start_idx.value() == 1
    assert main_window.end_idx.value() == 3
    assert main_window.cosmic_sigma.value() == 6.0
    assert main_window.cosmic_window.value() == 10
    assert main_window.cosmic_iterations.value() == 3
    assert main_window.cosmic_min.value() == 50.0


def test_config_table_operations(main_window, qtbot):
    """Test adding and removing rows from the configuration table."""
    initial_rows = main_window.config_table.rowCount()
    
    # Test adding a row
    main_window.add_config_row()
    assert main_window.config_table.rowCount() == initial_rows + 1
    
    # Test removing a row
    main_window.config_table.selectRow(main_window.config_table.rowCount() - 1)
    main_window.remove_config_row()
    assert main_window.config_table.rowCount() == initial_rows


def test_config_table_validation(main_window, qtbot):
    """Test validation of configuration table entries."""
    # Add a new row
    main_window.add_config_row()
    row = main_window.config_table.rowCount() - 1
    
    # Set valid values
    main_window.config_table.setItem(row, 0, main_window.config_table.item(row, 0).__class__("test"))
    main_window.config_table.setItem(row, 1, main_window.config_table.item(row, 1).__class__("2"))
    
    # Get configuration
    config = json.loads(main_window.get_config_json())
    assert "test" in config[0]
    assert config[0]["test"] == 2


def test_directory_browsing(main_window, qtbot, tmp_path, monkeypatch):
    """Test directory browsing functionality."""
    test_dir = tmp_path / "test_browse"
    test_dir.mkdir()
    
    # Mock QFileDialog.getExistingDirectory
    def mock_get_existing_directory(*args, **kwargs):
        return str(test_dir)
    
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", mock_get_existing_directory)
    
    # Test input directory browsing
    main_window.input_dir.clear()
    input_browse = main_window.findChildren(QPushButton)[0]  # First browse button
    qtbot.mouseClick(input_browse, Qt.MouseButton.LeftButton)
    assert main_window.input_dir.text() == str(test_dir)
    
    # Test output directory browsing
    main_window.output_dir.clear()
    output_browse = main_window.findChildren(QPushButton)[1]  # Second browse button
    qtbot.mouseClick(output_browse, Qt.MouseButton.LeftButton)
    assert main_window.output_dir.text() == str(test_dir)


def test_log_operations(main_window, qtbot):
    """Test log output operations."""
    # Test adding a message
    test_message = "Test log message"
    main_window.log(test_message)
    assert test_message in main_window.log_output.toPlainText()
    
    # Test adding an error message
    error_message = "Error: Test error"
    main_window.log(error_message)
    assert error_message in main_window.log_output.toPlainText()
    
    # Test clearing the log
    main_window.clear_log()
    assert main_window.log_output.toPlainText() == ""


def test_state_saving_and_loading(main_window, qtbot, tmp_path):
    """Test saving and loading application state."""
    # Modify some values
    main_window.prefix.setText("test_prefix")
    main_window.start_idx.setValue(5)
    main_window.end_idx.setValue(10)
    main_window.cosmic_sigma.setValue(7.0)
    
    # Save state
    main_window.save_state()
    
    # Create a new window
    new_window = MainWindow()
    qtbot.addWidget(new_window)
    
    # Load state
    new_window.load_state()
    
    # Check that values were loaded correctly
    assert new_window.prefix.text() == "test_prefix"
    assert new_window.start_idx.value() == 5
    assert new_window.end_idx.value() == 10
    assert new_window.cosmic_sigma.value() == 7.0


def test_conversion_controls(main_window, qtbot):
    """Test conversion control buttons."""
    # Initially, start button should be enabled and stop button disabled
    assert main_window.start_button.isEnabled()
    assert not main_window.stop_button.isEnabled()
    
    # Start conversion
    main_window.start_conversion()
    
    # After starting, start button should be disabled and stop button enabled
    assert not main_window.start_button.isEnabled()
    assert main_window.stop_button.isEnabled()
    
    # Stop conversion
    main_window.stop_conversion()
    
    # Wait for worker to finish
    if main_window.worker is not None:
        qtbot.waitUntil(lambda: not main_window.worker.isRunning(), timeout=5000)
        main_window.worker = None
    
    # After stopping, start button should be enabled and stop button disabled
    assert main_window.start_button.isEnabled()
    assert not main_window.stop_button.isEnabled()


def test_invalid_configuration_handling(main_window, qtbot):
    """Test handling of invalid configurations."""
    # Clear the configuration table
    while main_window.config_table.rowCount() > 0:
        # Select the first row before removing
        main_window.config_table.selectRow(0)
        main_window.remove_config_row()
    
    # Try to start conversion
    main_window.start_conversion()
    
    # Wait for worker to finish
    if main_window.worker is not None:
        qtbot.waitUntil(lambda: not main_window.worker.isRunning(), timeout=5000)
        main_window.worker = None
    
    # Check that an error message was logged
    log_text = main_window.log_output.toPlainText()
    assert "No valid configuration found" in log_text


def test_directory_validation(main_window, qtbot, tmp_path):
    """Test validation of input/output directories."""
    # Ensure we have a valid configuration first
    main_window.config_table.setItem(0, 0, QTableWidgetItem("center"))
    main_window.config_table.setItem(0, 1, QTableWidgetItem("2"))
    
    # Set non-existent input directory
    nonexistent_dir = str(tmp_path / "nonexistent")
    main_window.input_dir.setText(nonexistent_dir)

    # Try to start conversion
    main_window.start_conversion()

    # Wait for worker to finish
    if main_window.worker is not None:
        qtbot.waitUntil(lambda: not main_window.worker.isRunning(), timeout=5000)
        main_window.worker = None

    # Check that an error message was logged
    log_text = main_window.log_output.toPlainText()
    assert f"Error: Input directory not found - {nonexistent_dir}" in log_text 