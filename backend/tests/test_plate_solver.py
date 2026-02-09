import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.tools.capture_sky.tool import SkyCaptureTool
from src.config import AppConfig

class TestPlateSolver(unittest.TestCase):
    
    @patch("src.tools.capture_sky.tool.get_config_from_env")
    @patch("src.tools.capture_sky.tool.CustomRemotePlateSolver")
    @patch("src.tools.capture_sky.tool.AstrometryNetPlateSolver")
    def test_solver_initialization_custom(self, MockAstrometrySolver, MockCustomSolver, mock_get_config):
        # Setup config for custom solver
        mock_config = MagicMock(spec=AppConfig)
        mock_config.plate_solving_method = "custom_remote"
        mock_config.verbose = False
        mock_get_config.return_value = mock_config
        
        # Initialize tool
        tool = SkyCaptureTool()
        
        # Verify CustomRemotePlateSolver was initialized
        MockCustomSolver.assert_called_once_with(mock_config)
        MockAstrometrySolver.assert_not_called()
        self.assertEqual(tool.plate_solver, MockCustomSolver.return_value)
        
    @patch("src.tools.capture_sky.tool.get_config_from_env")
    @patch("src.tools.capture_sky.tool.CustomRemotePlateSolver")
    @patch("src.tools.capture_sky.tool.AstrometryNetPlateSolver")
    def test_solver_initialization_astrometry(self, MockAstrometrySolver, MockCustomSolver, mock_get_config):
        # Setup config for astrometry solver
        mock_config = MagicMock(spec=AppConfig)
        mock_config.plate_solving_method = "astrometry_net"
        mock_config.verbose = False
        mock_get_config.return_value = mock_config
        
        # Initialize tool
        tool = SkyCaptureTool()
        
        # Verify AstrometryNetPlateSolver was initialized
        MockAstrometrySolver.assert_called_once_with(mock_config)
        MockCustomSolver.assert_not_called()
        self.assertEqual(tool.plate_solver, MockAstrometrySolver.return_value)

    @patch("src.tools.capture_sky.tool.get_config_from_env")
    @patch("src.tools.capture_sky.tool.CustomRemotePlateSolver")
    def test_plate_solve_delegation(self, MockCustomSolver, mock_get_config):
        # Setup config
        mock_config = MagicMock(spec=AppConfig)
        mock_config.plate_solving_method = "custom_remote"
        mock_config.plate_solving_use_cache = False
        mock_config.storage_dir = "/tmp"
        mock_config.verbose = True
        mock_get_config.return_value = mock_config
        
        # Setup solver mock
        mock_solver_instance = MockCustomSolver.return_value
        mock_solver_instance.name = "MockSolver"
        expected_wcs = MagicMock()
        expected_wcs.__getitem__.return_value = 10.0 # Mock WCS values
        mock_solver_instance.solve.return_value = expected_wcs
        
        # Initialize tool
        tool = SkyCaptureTool()
        
        # Mock image
        mock_image = MagicMock()
        
        # Call _plate_solve
        # We need to access the private method for testing or test through public API?
        # _plate_solve is called by capture_sky. Let's call _plate_solve directly as it's what we modified.
        result = tool._plate_solve(mock_image)
        
        # Verify solve was called
        mock_solver_instance.solve.assert_called_once_with(mock_image)
        self.assertEqual(result, expected_wcs)

if __name__ == "__main__":
    unittest.main()
