import asyncio
import json
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

base_path = "../data/"  # Adjust if needed
# Load data
with open(base_path + "trains.json") as f:
    trains = json.load(f)


# ── Browser ────────────────────────────────────────────────────────────────────

url = "https://enquiry.indianrail.gov.in/mntes/"


async def init_browser(playwright):
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
    )
    return browser, await context.new_page()


async def init_schedule_page(page):
    await page.goto(url)
    await page.wait_for_selector("input[name='trainNo']", timeout=10000)
    await page.get_by_text("Train Schedule", exact=True).click()
    await page.wait_for_selector("input[name='trainNo']", timeout=10000)


async def fetch_schedule(page, train_no):
    await page.fill("input[name='trainNo']", "")
    await page.fill("input[name='trainNo']", str(train_no))

    async with page.expect_navigation(wait_until="load", timeout=15000):
        await page.click("input[value='Get Schedule']")

    try:
        await page.wait_for_selector("table tr td", timeout=10000)
    except Exception:
        return await page.content()

    await page.wait_for_timeout(500)
    return await page.content()


async def recover(page):
    await page.goto(url)
    await page.wait_for_selector("input[name='trainNo']", timeout=10000)
    await page.get_by_text("Train Schedule", exact=True).click()
    await page.wait_for_selector("input[name='trainNo']", timeout=10000)


# ── Parsing ────────────────────────────────────────────────────────────────────


def parse_train_info(table):
    """Extract metadata from the first table"""
    train_info = {}
    for row in table.find_all("tr"):
        tds = row.find_all("td")
        text = row.text.strip()

        if "Travel Time" in text:
            train_info["route"] = tds[0].text.strip() if tds else ""
            travel = tds[1].text.strip() if len(tds) > 1 else ""
            train_info["travel_time"] = travel.replace("Travel Time:", "").strip()

        elif "Days of Run" in text:
            train_info["days_of_run"] = (
                text.split("Days of Run:")[-1].split("Type:")[0].strip()
            )
            train_info["type"] = (
                text.split("Type:")[-1].strip() if "Type:" in text else ""
            )

        elif "Reserved Class of Travel" in text:
            train_info["reserved_class"] = (
                tds[0].text.replace("Reserved Class of Travel:", "").strip()
                if tds
                else ""
            )
            train_info["unreserved_class"] = (
                tds[1].text.replace("Un-Reserved Class :", "").strip()
                if len(tds) > 1
                else ""
            )

        elif "Un-Reserved Fare" in text:
            train_info["fare_category"] = (
                tds[0].text.replace("Un-Reserved Fare Category :", "").strip()
                if tds
                else ""
            )
            train_info["season_ticket"] = (
                tds[1].text.replace("Un-Reserved Season Ticket (MST) :", "").strip()
                if len(tds) > 1
                else ""
            )

    return train_info


def parse_stops(table):
    """Extract stops from the schedule table"""
    stops = []
    for row in table.find_all("tr")[1:]:
        tds = row.find_all("td")
        if len(tds) < 6:
            continue

        fonts = tds[1].find_all("font")
        time_fonts = tds[3].find_all("font")

        stops.append(
            {
                "sr": tds[0].text.strip(),
                "station_name": fonts[0].text.strip() if len(fonts) > 0 else "",
                "station_code": fonts[1].text.strip() if len(fonts) > 1 else "",
                "day": tds[2].text.strip(),
                "arrival": time_fonts[0].text.strip() if len(time_fonts) > 0 else "",
                "departure": time_fonts[1].text.strip() if len(time_fonts) > 1 else "",
                "halt": tds[4].text.strip(),
                "distance_km": tds[5].text.strip(),
            }
        )
    return stops


def parse_schedule(html):
    soup = BeautifulSoup(html, "html.parser")
    train_info = {}
    stops = []

    for table in soup.find_all("table"):
        first_row = table.find("tr")
        if not first_row:
            continue

        if "Days of Run" in table.text and "Travel Time" in table.text:
            train_info = parse_train_info(table)

        elif "Station" in first_row.text:
            stops = parse_stops(table)

    return train_info, stops


# ── Persistence ────────────────────────────────────────────────────────────────


def save_progress(all_schedules):
    with open(base_path + "schedules_progress.json", "w") as f:
        json.dump(all_schedules, f, indent=2, ensure_ascii=False)


def save_final(all_schedules, failed):
    with open(base_path + "schedules.json", "w") as f:
        json.dump(all_schedules, f, indent=2, ensure_ascii=False)

    if failed:
        with open(base_path + "failed_trains.json", "w") as f:
            json.dump(failed, f, indent=2)


# ── Main ───────────────────────────────────────────────────────────────────────


async def process_trains(page):
    all_schedules = {}
    failed = []

    for i, train in enumerate(trains):
        train_no = train["TrainNo"]
        train_name = train["TrainName"]

        try:
            html = await fetch_schedule(page, train_no)
            train_info, stops = parse_schedule(html)

            if stops:
                all_schedules[train_no] = {
                    "train_name": train_name,
                    "info": train_info,
                    "stops": stops,
                }

            print(
                f"[{i + 1}/{len(trains)}] {train_no} - {train_name}: {len(stops)} stops"
            )

        except Exception as e:
            print(f"  Failed {train_no}: {e}")
            failed.append(train_no)
            if "Target page, context or browser has been closed" in str(e):
                await recover(page)

        if (i + 1) % 100 == 0:
            save_progress(all_schedules)
            print(f"  Progress saved — {len(all_schedules)} trains")

    return all_schedules, failed


async def main():
    async with async_playwright() as p:
        browser, page = await init_browser(p)

        print("Initialising schedule page...")
        await init_schedule_page(page)
        print("Ready!\n")

        all_schedules, failed = await process_trains(page)

        await browser.close()

    save_final(all_schedules, failed)

    print("\nDone!")
    print(f"Trains processed : {len(all_schedules)}")
    print(f"Failed           : {len(failed)}")


asyncio.run(main())
