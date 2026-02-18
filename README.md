# Railway Data Scraper

A Python project for downloading and processing Indian Railways data, including station information and train schedules.

## Overview

This project scrapes data from Indian Railways' official sources to extract:
- Railway station details (names, codes, coordinates, layer depth)
- Train information (train numbers and names)

The data is saved in both JSON and CSV formats for easy consumption.

## Features

- Downloads station data from Indian Railways map service
- Extracts train list from Indian Railways enquiry system
- Saves data in structured JSON format
- Supports CSV export for station data
- Automatic data directory creation
- Robust error handling with proper HTTP headers

## Project Structure

```
.
├── data/
│   ├── stations.json    # Station data (7000+ stations)
│   ├── trains.json      # Train data (20000+ trains)
│   └── *.csv           # CSV exports (optional)
├── main.py             # Entry point (placeholder)
├── train_data.py       # Main data extraction class
└── railway-map.ipynb   # Jupyter notebook for analysis
```

## Installation

1. Ensure Python 3.13+ is installed
2. Install dependencies:
```bash
pip install requests
```

## Usage

### Extract All Data

Run the main script to download both stations and trains:

```bash
python train_data.py
```

This will:
1. Download station data from the Indian Railways map service
2. Extract and save ~7000+ stations to `data/stations.json`
3. Download train data from the enquiry system
4. Extract and save ~20000+ trains to `data/trains.json`

### Use as a Module

```python
from train_data import TrainData

# Extract stations
station_url = "https://indianrailways.gov.in/index/index_data/data.js"
station_scraper = TrainData(station_url, data_type="stations")
stations = station_scraper.extract_stations()

# Extract trains
from datetime import datetime
today = datetime.now().strftime("%Y%m%d")
trains_url = f"https://enquiry.indianrail.gov.in/mntes/javascripts/train_data.js?v={today}10"
train_scraper = TrainData(trains_url, data_type="trains")
trains = train_scraper.extract_trains()
```

## Data Format

### Stations
```json
{
  "Station": "Angul",
  "StationCode": "ANGL",
  "ctrX": 5295.74,
  "ctrY": 5194.48,
  "layer_depth": 1
}
```

### Trains
```json
{
  "TrainNo": "12345",
  "TrainName": "EXAMPLE EXPRESS"
}
```

## Requirements

- Python 3.13+
- requests library
- Internet connection for data downloads

## Notes

- Train data URL includes a timestamp that updates daily at 10 AM
- Station coordinates (ctrX, ctrY) are in the Indian Railways map coordinate system
- Some stations may have "*" or "-" as station codes (incomplete data)

## Suggestions for Improvement

### Code Quality
1. **Add dependency management**: Update `pyproject.toml` to include `requests` in dependencies
2. **Error handling**: Add retry logic for network failures
3. **Logging**: Replace print statements with proper logging module
4. **Type hints**: Add type annotations for better code clarity
5. **Configuration**: Move URLs and constants to a config file or environment variables

### Features
1. **CLI interface**: Add argparse for command-line options (--stations-only, --trains-only, --output-format)
2. **Data validation**: Validate extracted data before saving
3. **Incremental updates**: Check if data already exists and only update if needed
4. **Data analysis**: Implement search/filter functions for stations and trains
5. **API wrapper**: Create a simple API to query the downloaded data

### Architecture
1. **Separate concerns**: Split TrainData class into StationScraper and TrainScraper
2. **Abstract base class**: Create a BaseScraper for common functionality
3. **Data models**: Use dataclasses or Pydantic for data validation
4. **Database support**: Add SQLite storage option for better querying
5. **Caching**: Implement caching to avoid repeated downloads

### Testing
1. **Unit tests**: Add tests for extraction logic
2. **Mock responses**: Test with mock HTTP responses
3. **Integration tests**: Test end-to-end data flow
4. **CI/CD**: Set up GitHub Actions for automated testing

### Documentation
1. **Docstrings**: Add comprehensive docstrings to all methods
2. **API documentation**: Generate docs with Sphinx
3. **Examples**: Add more usage examples and use cases
4. **Contributing guide**: Add CONTRIBUTING.md for contributors
