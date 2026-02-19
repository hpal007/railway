import asyncio
import json
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

# Load data
with open("data/trains.json") as f:
    trains = json.load(f)

with open("data/stations.json") as f:
    stations = json.load(f)

valid_codes = {s["code"] for s in stations}


# ── Parsing ────────────────────────────────────────────────────────────────────


def parse_schedule(html):
    soup = BeautifulSoup(html, "html.parser")

    for table in soup.find_all("table"):
        first_row = table.find("tr")
        if not first_row or "Station" not in first_row.text:
            continue

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
                    "arrival": time_fonts[0].text.strip()
                    if len(time_fonts) > 0
                    else "",
                    "departure": time_fonts[1].text.strip()
                    if len(time_fonts) > 1
                    else "",
                    "halt": tds[4].text.strip(),
                    "distance_km": tds[5].text.strip(),
                }
            )
        return stops

    return []


def build_edges(stops):
    edges = set()
    for i in range(len(stops) - 1):
        a = stops[i]["station_code"]
        b = stops[i + 1]["station_code"]
        if a in valid_codes and b in valid_codes:
            edges.add((a, b))
    return edges


# ── Browser ────────────────────────────────────────────────────────────────────


async def init_browser(playwright):
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
    )
    return browser, await context.new_page()


async def init_schedule_page(page):
    await page.goto("https://enquiry.indianrail.gov.in/mntes/")
    await page.wait_for_selector("input[name='trainNo']", timeout=10000)
    await page.get_by_text("Train Schedule", exact=True).click()
    await page.wait_for_selector("input[name='trainNo']", timeout=10000)


async def fetch_schedule(page, train_no):
    await page.fill("input[name='trainNo']", "")
    await page.fill("input[name='trainNo']", str(train_no))
    await page.click("input[value='Get Schedule']")

    try:
        # Wait for a table that has actual rows with station data
        await page.wait_for_selector("table tr td", timeout=10000)
    except Exception:
        # No schedule found for this train (special/test trains)
        return await page.content()

    await page.wait_for_timeout(500)
    return await page.content()


async def recover(page):
    await page.goto("https://enquiry.indianrail.gov.in/mntes/")
    await page.wait_for_selector("input[name='trainNo']", timeout=10000)
    await page.get_by_text("Train Schedule", exact=True).click()
    await page.wait_for_selector("input[name='trainNo']", timeout=10000)


# ── Persistence ────────────────────────────────────────────────────────────────


def save_progress(all_schedules):
    with open("data/schedules_progress.json", "w") as f:
        json.dump(all_schedules, f, indent=2, ensure_ascii=False)


def save_final(all_schedules, failed):
    with open("data/schedules.json", "w") as f:
        json.dump(all_schedules, f, indent=2, ensure_ascii=False)

    if failed:
        with open("data/failed_trains.json", "w") as f:
            json.dump(failed, f, indent=2)


# ── Main ───────────────────────────────────────────────────────────────────────


async def process_trains(page):
    all_schedules = {}
    
    failed = []

    for i, train in enumerate(trains[:5]):

        train_no = train["TrainNo"]
        train_name = train["TrainName"]

        try:
            html = await fetch_schedule(page, train_no)
            stops = parse_schedule(html)

            if stops:
                all_schedules[train_no] = {"train_name": train_name, "stops": stops}
               

            print(
                f"[{i + 1}/{len(trains)}] {train_no} - {train_name}: {len(stops)} stops"
            )

        except Exception as e:
            print(f"  Failed {train_no}: {e}")
            failed.append(train_no)
            # Only recover on serious failures, not missing schedules
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
