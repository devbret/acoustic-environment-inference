# Acoustic Environment Inference Visualizer

![Screenshot of the Acoustic Environment Inference Visualizer.](https://hosting.photobucket.com/bbcfb0d4-be20-44a0-94dc-65bff8947cf2/936bb102-1139-4936-947b-b1fa9f3293be.png)

An OSINT Python toolkit designed to analyze and compare the acoustic signatures of audio and video recordings.

## Overview

The application extracts a variety of environmental and technical features to characterize the likely recording environment. To these ends, each file’s metadata and derived measurements are summarized into a unified JSON report.

The system also performs comparisons between recordings to estimate the likelihood of having been captured in the same physical space.

A lightweight D3-powered web interface visualizes these results. Showing per-file acoustic profiles and ranked match tables for side-by-side comparison.

The pipeline is designed for reproducibility and transparency. Accomplished by using open standards and common scientific libraries like librosa, scipy and numpy. While relying on ffmpeg for cross-format media extraction.

Together, this makes the tool a self-contained forensic aid and research utility for field analysts, investigative journalists or acoustic researchers interested in environment inference, provenance validation or cross-recording matching.

## Set Up Instructions

Below are the required software programs and instructions for installing and using this application.

### Programs Needed

- [Git](https://git-scm.com/downloads)

- [Python](https://www.python.org/downloads/)

### Steps For Use

1. Install the above programs

2. Open a terminal

3. Clone this repository using `git` by running the following command: `git clone git@github.com:devbret/acoustic-environment-inference.git`

4. Navigate to the repo's directory by running: `cd acoustic-environment-inference`

5. Create a virtual environment with this command: `python3 -m venv venv`

6. Activate your virtual environment using: `source venv/bin/activate`

7. Install the needed dependencies for running the script: `pip install -r requirements.txt`

8. Place your audio files into the `input` directory

9. Run the program using this command: `python3 app.py`

10. Launch the application's frontend by starting a Python server with the following command: `python3 -m http.server`

11. Access the user interface in a browser by visiting: `http://localhost:8000`

12. To exit the virtual environment (venv), type this command in the terminal: `deactivate`

## Other Considerations

This project repo is intended to demonstrate an ability to do the following:

- Analyze audio and video files to detect traits and likely recording environment

- Compare analyzed media files against the others and generate scored similarity matches

If you have any questions or would like to collaborate, please reach out either on GitHub or via [my website](https://bretbernhoft.com/).
