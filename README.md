# Acoustic Environment Inference

![Screenshot of the Acoustic Environment Inference Visualizer.](https://hosting.photobucket.com/bbcfb0d4-be20-44a0-94dc-65bff8947cf2/936bb102-1139-4936-947b-b1fa9f3293be.png)

An OSINT Python toolkit designed to analyze and compare the acoustic signatures of audio and video recordings.

## Overview

The application extracts a variety of environmental and technical features to characterize the likely recording environment. To these ends, each file’s metadata and derived measurements are summarized into a unified JSON report.

The system also performs comparisons between recordings to estimate the likelihood of having been captured in the same physical space.

A lightweight D3-powered web interface visualizes these results. Showing per-file acoustic profiles and ranked match tables for side-by-side comparison.

The pipeline is designed for reproducibility and transparency. Accomplished by using open standards and common scientific libraries like librosa, scipy and numpy. While relying on ffmpeg for cross-format media extraction.

Together, this makes the tool a self-contained forensic aid and research utility for field analysts, investigative journalists or acoustic researchers interested in environment inference, provenance validation or cross-recording matching.
