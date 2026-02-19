from datetime import datetime
from train_data import TrainData


def main():
    today = datetime.now().strftime("%Y%m%d")

    # indianrailways.gov.in includes: All passenger stations, Freight/goods only stations, Halt stations, proposed/under construction stations, industrial sidings
    station_url = "https://indianrailways.gov.in/index/index_data/data.js"
    indianrailways_station = TrainData(station_url, data_type="indianrailways_stations")
    indianrailways_station = (
        indianrailways_station.extract_stations_from_indianrailways()
    )
    print(f"Total stations found from indianrailways: {len(indianrailways_station)}")

    # Stations relevant for passenger enquiry system. This includes only passenger stations and halts
    station_url = f"https://enquiry.indianrail.gov.in/mntes/javascripts/station_data.js?v={today}08"  # Update record on 10AM daily

    station_list = TrainData(station_url, data_type="stations")
    stations = station_list.extract_stations()
    print(f"Total stations found: {len(stations)}")

    # Train
    trains_url = f"https://enquiry.indianrail.gov.in/mntes/javascripts/train_data.js?v={today}10"  # Update record on 10AM daily
    trains = TrainData(trains_url, data_type="trains")
    train_list = trains.extract_trains()
    print(f"Total trains found: {len(train_list)}")


if __name__ == "__main__":
    main()
