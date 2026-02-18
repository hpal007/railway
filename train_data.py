import requests
import json
import csv
from datetime import datetime
import re
import os


class TrainData:
    def __init__(self, url, data_type="stations"):
        self.url = url
        self.data_type = data_type
        os.makedirs("data", exist_ok=True)

    def download_data(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://indianrailways.gov.in/index/index.html",
            "Accept": "*/*",
        }

        print(f"Downloading {self.data_type} data...")
        response = requests.get(self.url, headers=headers, timeout=60)
        response.raise_for_status()  # raises error if download fails

        print(f"Downloaded successfully! File size: {len(response.text) / 1024:.1f} KB")
        return response.text

    def save_to_csv(self, stations):
        path = f"data/{self.data_type}.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=["Station", "StationCode", "ctrX", "ctrY", "layer_depth"]
            )
            writer.writeheader()
            writer.writerows(stations)
        print(f"Saved {len(stations)} stations to {self.data_type}.csv")

    def save_to_json(self, stations):
        path = f"data/{self.data_type}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(stations, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(stations)} stations to {self.data_type}.json")

    def extract_stations(self):
        content = self.download_data()
        data = json.loads(content)
        stations = []

        for layer in data["layers"]:
            layer_depth = layer.get("depth")
            for feature in layer.get("features", []):
                attrs = feature.get("attributes", {})
                station = {
                    "Station": attrs.get("Station", ""),
                    "StationCode": attrs.get("StationCod", ""),
                    "ctrX": feature.get("ctrX"),
                    "ctrY": feature.get("ctrY"),
                    "layer_depth": layer_depth,
                }
                stations.append(station)

        self.save_to_json(stations)
        return stations

    def extract_trains(self):
        # Extract the array content
        content = self.download_data()
        match = re.search(r"arrTrainList\s*=\s*\[(.*?)\]", content, re.DOTALL)
        if not match:
            raise ValueError("Could not find arrTrainList in response")

        # Extract all quoted strings
        raw_list = re.findall(r'"(.*?)"', match.group(1))

        trains = []
        for entry in raw_list:
            # Format is "00001- TRAIN NAME"
            parts = entry.split("- ", 1)
            if len(parts) == 2:
                trains.append(
                    {"TrainNo": parts[0].strip(), "TrainName": parts[1].strip()}
                )

        self.save_to_json(trains)
        return trains


if __name__ == "__main__":
    station_url = "https://indianrailways.gov.in/index/index_data/data.js"

    station = TrainData(station_url, data_type="stations")
    stations = station.extract_stations()
    print(f"Total stations found: {len(stations)}")

    # Train
    today = datetime.now().strftime("%Y%m%d")
    trains_url = f"https://enquiry.indianrail.gov.in/mntes/javascripts/train_data.js?v={today}10"  # Update record on 10AM daily
    trains = TrainData(trains_url, data_type="trains")
    train_list = trains.extract_trains()
    print(f"Total trains found: {len(train_list)}")
