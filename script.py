import argparse
import csv
import os

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry
import time
from bs4 import BeautifulSoup
import concurrent.futures


def getCoursesSession(cookie: str) -> requests.Session:
    retry_strategy = Retry(
        total=5,
        status_forcelist=[429, 500, 502, 503, 504],
        backoff_factor=4,
        allowed_methods=["HEAD", "GET", "OPTIONS"],
        )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.cookies.set("MoodleSession", cookie)

    return session


def getProfile(session: requests.Session, id: int) -> dict[str, str]:
    url = f"https://courses.finki.ukim.mk/user/profile.php?id={id}&showallcourses=1"
    response = session.get(url)

    if response.status_code != 200:
        return {}

    soup = BeautifulSoup(response.text, "html.parser")

    profile: dict[str, str] = {}
    sections = soup.select("#region-main > div > div > div.profile_tree > section")

    if len(sections) == 0:
        return {}
    profile["ID"] = id
    profile["URL"] = url
    profile["Name"] = soup.select_one(
        "#page-header > div > div > div > div.d-flex.align-items-center > div.mr-auto > div > div.page-header-headings > h1"
        ).text
    sections = soup.select("div.profile_tree")[0].select('section')

    containsEmail = any('Email address' in tag.get_text() for tag in sections)
    if containsEmail == True:
        if len(sections[0].findAll('a')) == 1:
            profile["Email"] = sections[0].find('a').text
        else:
            email_address = ""
            links = sections[0].findAll('a')
            for link in links:
                href_value = link.get('href', '')
                if href_value.startswith('mailto:'):
                    email_address = link.get_text()
                    break
            profile["Email"] = email_address
    else:
        profile["Email"] = "NA"
    profile["LastAccess"] = soup.find('dt', string='Last access to site').find_parent('dl').find('dd').text
    courses_tags = soup.select("ul > li > dl > dd > ul > li")
    courses = ""
    for course in courses_tags:
        courses += (course.text + "\n")
    profile["Courses"] = courses
    return profile


def getProfiles(session: requests.Session, lower: int, upper: int, threads: int) -> list[dict[str, str]]:
    print("Scraping data...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        tasks = []
        for i in range(lower, upper + 1):
            task = executor.submit(getProfile, session, i)
            tasks.append(task)
        profiles = []
        percentageComplete = 0
        num = 0
        for completed_task in concurrent.futures.as_completed(tasks):
            profile = completed_task.result()
            if profile == {}:
                continue
            profiles.append(profile)
            if upper == lower:
                percentageComplete = 0
            else:
                percentageComplete = float(num / (upper - lower))
            num += 1
            if num % 150 == 0:
                print(f'{(100 * percentageComplete):.2f}% of profiles scraped(id of {lower + num} to {upper})')
    print("Scraping completed")
    return profiles


def saveProfileToCSV(profile, path):
    with open(path, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['ID', 'URL', 'Name', 'Email', 'LastAccess', 'Courses'])
        writer.writerow(profile)


def main() -> None:

    parser = argparse.ArgumentParser(description="Scrape Courses profiles")

    parser.add_argument("-cookie", type=str, required=True, help="Courses session cookie")
    parser.add_argument("-lower", type=int, required=True, help="Lower index bound")
    parser.add_argument("-upper", type=int, required=True, help="Upper index bound")
    parser.add_argument("-threads", type=int, default="10", help="Number of threads to use")

    args = parser.parse_args()
    if args.lower > args.upper:
        temp = args.lower
        args.lower = args.upper
        args.upper = temp

    session = getCoursesSession(args.cookie)

    start = time.time()

    profiles = getProfiles(session, args.lower, args.upper, args.threads)

    csv_file_path = os.getcwd() + "\\data.csv"
    if not os.path.isfile(csv_file_path):
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=['ID', 'URL', 'Name', 'Email', 'LastAccess', 'Courses'])
            writer.writeheader()
    print("Saving data to CSV " + csv_file_path)
    for profile in profiles:
        saveProfileToCSV(profile, csv_file_path)
    print(f"Finished in {(time.time() - start):.3f} seconds")


if __name__ == "__main__":
    main()
