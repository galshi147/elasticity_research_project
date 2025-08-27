# Elasticity Research Project

A Python-based research tool for analyzing particle trajectories and vector fields in elasticity experiments using computer vision and particle tracking methods.

## Overview
The physical system exemined is a circular frame filled with little Clear-Flex disks and a silicon disk at the center which inflates
and by that create stress in the system and an elastic respond.
This project provides a comprehensive suite of tools for:
- Particle detection (disks centers') and tracking in image sequences
- Displacement measurement and calculation
- Vector field analysis (displacement field) and visualization
- Interactive GUI for real-time analysis

## Project Structure

```
elasticity_research_project/
├── main.py                     # Main entry point
├── requirements.txt            # Python dependencies
├── README.md                   # This file
│
├── Core Analysis Modules:
├── calculator.py               # Mathematical calculations and computations
├── detection_lib.py            # Particle detection algorithms
├── kdt_method.py               # K-D Tree Algorithm based particle tracking
├── piv_method.py               # Particle Image Velocimetry (PIV) based particle tracking
├── measurements_detectors.py   # Measurement data handling
├── visualization.py            # Plotting and visualization utilities
├── project_tools.py            # Common project utilities
├── programs.py                 # Test programs and examples
│
├── GUI Components:
├── gui_files/
│   ├── gui.py                  # Main GUI application
│   ├── gui_resources.py        # Base window classes and resources
│   ├── gui_scripts.py          # Animation and scripting functionality
│   ├── dialogs.py              # Dialog boxes for user input
│   ├── particle_tracker.py     # Particle tracking GUI window
│   ├── vec_field_analyzer.py   # Vector field analysis GUI window
│   ├── scripter.py             # Base scripting functionality
│   └── welcome_window.py       # Welcome/startup window
│
└── measurements/              # Experimental data directory
    └── 26.01.25/              # Date-organized measurement folders
        ├── raw_data/          # Original images
        ├── dot/               # Processed dot images (centers of disks)
        ├── graph/             # Generated graphs and plots
        ├── vector_field/      # Vector field data files
        └── *.pkl              # Saved measurement data
```

## Features

### Particle Tracking
- **K-D Tree Method**: Efficient nearest-neighbor particle matching across frames
- **PIV Method**: Particle Image Velocimetry for flow field analysis
- **Trajectory Building**: Automatic particle trajectory construction
- **Interactive Visualization**: Real-time plotting with zoom and pan capabilities

### Vector Field Analysis
- **Displacement Calculation**: Compute particle displacements between frames
- **Vector Field Visualization**: Interactive vector field plotting
- **Radial Displacement Analysis**: Specialized radial displacement measurements
- **Animation Support**: Time-lapse animations of particle motion

### GUI Features
- **Multi-Window Interface**: Separate windows for different analysis types
- **Real-time Controls**: Interactive frame selection and parameter adjustment
- **Zoom and Pan**: Mouse wheel zoom and drag-to-pan functionality
- **Export Capabilities**: Save images, videos, and data
- **Scripting Support**: Automated analysis sequences

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd elasticity_research_project
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Required Python packages**:
   - PySide6 (GUI framework)
   - matplotlib (plotting and visualization)
   - numpy (numerical computations)
   - opencv-python (computer vision)
   - scipy (scientific computing)
   - scikit-learn (KDTree implementation)

## Usage

### Basic Usage
```python
from measurements_detectors import Measure
from gui_files.gui import Gui

# Create a measurement instance
measure = Measure("26.01.25", path_setting='local')

# Launch the GUI
gui = Gui(measure, "Kdt")
gui.run()
```

### Programmatic Analysis
```python
from kdt_method import Kdt
from visualization import Plotter

# Initialize tracking method
kdt = Kdt(measure)

# Build particle trajectories
trajectories = kdt.build_trajectories()

# Visualize results
plotter = Plotter(measure, source='local')
plotter.plot_particles_trajectories(ax, trajectories)
```

## Analysis Methods

### K-D Tree Particle Tracking
- Efficient nearest-neighbor matching
- Handles particle appearance/disappearance
- Configurable distance thresholds
- Memory-efficient trajectory storage

### PIV Analysis
- Cross-correlation based velocity estimation
- Grid-based analysis regions
- Interpolation for smooth vector fields
- Statistical validation of results

### Displacement Analysis
- Frame-to-frame displacement calculation
- Radial displacement measurements
- Temporal displacement tracking
- Statistical analysis of motion patterns

## GUI Controls

### Frame Selection
- **Frame1/Frame2**: Define analysis range
- **Base Jump**: Step size for frame advancement
- **Interval**: Sampling interval for analysis

### Visualization
- **Mouse Wheel**: Zoom in/out on plots
- **Left Click + Drag**: Pan around zoomed plots
- **Reset Zoom**: Return to default view
- **Smooth Mode**: Toggle smooth/discrete visualization

### Animation Scripts
- **K-Buffer Animation**: Sliding window analysis
- **Trajectory Animation**: Particle path visualization
- **Parameter Sweeps**: Automated parameter exploration

## Data Format

### Input Images
- Supported formats: JPG, PNG, TIFF
- Naming convention: `DSC_XXXX.jpg` (where XXXX is frame number)
- Organized in date-specific folders

### Output Data
- **Vector Fields**: Text files with displacement vectors
- **Trajectories**: Numpy arrays with particle positions
- **Measurements**: Pickle files with complete analysis results
- **Visualizations**: PNG/JPG images and MP4 videos

## Configuration

### Measurement Setup
```python
# Local data processing
measure = Measure("26.01.25", path_setting='local')

# Network drive processing
measure = Measure("26.01.25", path_setting='drive')
```

### Analysis Parameters
- Detection thresholds in `detection_lib.py`
- Tracking parameters in `kdt_method.py`
- Visualization settings in `visualization.py`


## Research Applications

This tool is designed for elasticity research applications including:
- Material deformation analysis
- Strain field measurements
- Dynamic loading experiments
- Particle tracking in soft materials
- Flow visualization studies

