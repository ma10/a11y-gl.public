import os
import pytest
import tempfile
import shutil
from pathlib import Path
from freee_a11y_gl.initializer import (
    ls_dir,
    read_file_content,
    read_yaml_file,
    handle_file_error
)


class TestLsDir:
    def setup_method(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        
        # Create some test files in the temporary directory
        self.create_test_files([
            'file1.txt',
            'file2.txt',
            'file3.json',
            'subfolder/file4.txt',
            'subfolder/file5.json',
        ])
        
    def teardown_method(self):
        # Clean up the temporary directory after the test
        shutil.rmtree(self.temp_dir)
        
    def create_test_files(self, file_paths):
        """Helper to create test files in temp directory"""
        for file_path in file_paths:
            # Create full path
            full_path = os.path.join(self.temp_dir, file_path)
            # Ensure parent directory exists
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            # Create an empty file
            with open(full_path, 'w') as f:
                f.write(f"Content of {file_path}")
    
    def test_ls_dir_lists_all_files(self):
        """Test that ls_dir lists all files when no extension is provided"""
        files = ls_dir(self.temp_dir)
        
        # Should find all 5 files
        assert len(files) == 5
        
        # Check that all expected files are found
        expected_files = {'file1.txt', 'file2.txt', 'file3.json', 
                         'subfolder/file4.txt', 'subfolder/file5.json'}
        
        # Convert full paths to relative paths for comparison
        relative_files = {os.path.relpath(f, self.temp_dir) for f in files}
        
        # Check that all expected files are found (ignoring exact path format)
        for expected in expected_files:
            assert any(expected in f for f in relative_files)
    
    def test_ls_dir_with_extension_filter(self):
        """Test filtering by extension"""
        # Get only .txt files
        txt_files = ls_dir(self.temp_dir, extension='.txt')
        
        # Should find 3 txt files
        assert len(txt_files) == 3
        
        # Check that all files end with .txt
        for file_path in txt_files:
            assert file_path.endswith('.txt')
        
        # Get only .json files
        json_files = ls_dir(self.temp_dir, extension='.json')
        
        # Should find 2 json files
        assert len(json_files) == 2
        
        # Check that all files end with .json
        for file_path in json_files:
            assert file_path.endswith('.json')
    
    def test_ls_dir_nonexistent_directory(self):
        """Test behavior with non-existent directory"""
        non_existent_dir = os.path.join(self.temp_dir, "does_not_exist")
        
        # Should raise FileNotFoundError
        with pytest.raises(FileNotFoundError) as excinfo:
            ls_dir(non_existent_dir)
        
        # Check error message
        assert f"Directory not found: {non_existent_dir}" in str(excinfo.value)


class TestReadFileContent:
    def setup_method(self):
        # Create a temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8')
        self.temp_file.write("Test content")
        self.temp_file.close()
        
    def teardown_method(self):
        # Remove the temporary file after the test
        os.unlink(self.temp_file.name)
        
    def test_read_file_content(self):
        """Test reading content from a file"""
        content = read_file_content(self.temp_file.name)
        assert content == "Test content"
        
    def test_read_nonexistent_file(self):
        """Test behavior with non-existent file"""
        non_existent_file = self.temp_file.name + "_nonexistent"
        
        # Should raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            read_file_content(non_existent_file)


# Note: handle_file_error and other functions that use sys.exit() should be tested 
# with additional test techniques to capture exit or using mocks.
# Here's a simplified example to demonstrate:

def test_handle_file_error(monkeypatch, capsys):
    """Test that handle_file_error prints error message and exits"""
    # Mock sys.exit to avoid actually exiting
    def mock_exit(code):
        pass
    
    monkeypatch.setattr("sys.exit", mock_exit)
    
    # Call the function
    handle_file_error(Exception("Test error"), "/path/to/file")
    
    # Check output
    captured = capsys.readouterr()
    assert "Error with file /path/to/file: Test error" in captured.err
