import requests
import json
import csv

def download_data(url, save_path="data.js"):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://indianrailways.gov.in/index/index.html",
        "Accept": "*/*",
    }
    
    print("Downloading data.js...")
    response = requests.get(url, headers=headers, timeout=60)
    response.raise_for_status()  # raises error if download fails
    
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(response.text)
    
    print(f"Downloaded successfully! File size: {len(response.text) / 1024:.1f} KB")
    return response.text

def extract_stations(content):
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
                "layer_depth": layer_depth
            }
            stations.append(station)

    return stations

def save_to_csv(stations, path="stations.csv"):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Station", "StationCode", "ctrX", "ctrY", "layer_depth"])
        writer.writeheader()
        writer.writerows(stations)
    print(f"Saved {len(stations)} stations to {path}")

def save_to_json(stations, path="stations.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(stations, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(stations)} stations to {path}")


# --- Run ---
URL = "https://indianrailways.gov.in/index/index_data/data.js"

content = download_data(URL)
stations = extract_stations(content)
print(f"Total stations found: {len(stations)}")

# save_to_csv(stations)
save_to_json(stations)