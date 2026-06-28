# Acoustic Environment Inference Visualizer

![Screenshot of the Acoustic Environment Inference Visualizer.](https://hosting.photobucket.com/bbcfb0d4-be20-44a0-94dc-65bff8947cf2/936bb102-1139-4936-947b-b1fa9f3293be.png)

Analyze media files to extract environmental sound fingerprints, then display the results with interactive D3 visualizations.

## Application Overview

Extracts a variety of environmental and technical features to characterize the likely recording environment. To these ends, each file’s metadata and measurements are summarized into a unified JSON report. The system also performs comparisons between recordings to estimate the likelihood of having been captured in the same physical space.

A lightweight D3-powered web interface visualizes these results. Showing per-file acoustic profiles and ranked match tables for side-by-side comparison.

The pipeline is designed for reproducibility and transparency. Accomplished by using open standards and common scientific libraries like librosa, scipy and numpy. While relying on ffmpeg for cross-format media extraction.

Together, this makes the tool a self-contained forensic aid and research utility for field analysts, investigative journalists or acoustic researchers interested in environment inference, provenance validation or cross-recording matching.

## Basic Setup Instructions

Below are the required software programs and instructions for installing and using this application on a Linux machine.

### Programs Needed

- [Git](https://git-scm.com/downloads)

- [Python](https://www.python.org/downloads/)

- [FFmpeg](https://ffmpeg.org/download.html)

### Steps For Use

1. Install the above programs

2. Open a terminal

3. Clone this repository: `git clone git@github.com:devbret/acoustic-environment-inference.git`

4. Navigate to the repo's directory: `cd acoustic-environment-inference`

5. Create a virtual environment: `python3 -m venv venv`

6. Activate your virtual environment: `source venv/bin/activate`

7. Install the needed dependencies: `pip install -r requirements.txt`

8. Place your media files into the `input` directory

9. Run the Python script: `python3 app.py`

10. Launch an HTTP server: `python3 -m http.server`

11. Access the user interface in a browser: `http://localhost:8000`

12. Once finished, exit the HTTP server: `CTRL + c`

13. Exit the virtual environment: `deactivate`

## Other Considerations

This project repo is intended to demonstrate an ability to do the following:

- Analyze media files to identify environmental sound characteristics and compare recordings for similarity

- Investigate how recordings may relate by analyzing background noise, reverberation and shared fingerprints

- Process audio and visualize the results with charts, tables and a network graph

If you have any questions or would like to collaborate, please reach out either on GitHub or via [my website](https://bretbernhoft.com/).
