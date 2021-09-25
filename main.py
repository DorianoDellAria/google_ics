from ics import Calendar
import requests
from Google import Create_Service, convert_to_RFC_datetime
from typing import List
from converter import ics_to_google_event
from time import sleep
import schedule
from dotenv import load_dotenv
import os

if not load_dotenv():
    print('Can\'t find .env file')
    exit(1)

CLIENT_SECRET_FILE = 'creds.json'
API_SERVICE_NAME = 'calendar'
API_VERSION = 'v3'
SCOPES = ['https://www.googleapis.com/auth/calendar.events',
          'https://www.googleapis.com/auth/calendar']

CALENDAR_ID = os.getenv('CAL_ID')
URL_ICS = os.getenv('URL_ICS')
Q1 = [*[f'S-INFO-0{x}' for x in [21, 26, 28, 23]], 'I-ILIA-208']
Q2 = [*[f'S-INFO-{x}' for x in ['044', '027', '810', '075', ]], 'I-ILIA-011']
CURSUS = [*Q1, *Q2]
MAX_BACKOFF = 120


def get_filtered_calendar(url: str, filter: List[str]) -> Calendar:
    raw_ics = requests.get(url).text
    c = Calendar(raw_ics)
    filtered_calendar = Calendar()
    for event in c.timeline:
        id = event.name.split(' - ')[0]
        if id in filter:
            filtered_calendar.events.add(event)
    return filtered_calendar


def get_google_calendar(service):
    page_token = None
    event_list = []
    while True:
        list_of_events = service.events().list(
            calendarId=CALENDAR_ID, pageToken=page_token).execute()
        event_list += list_of_events['items']
        page_token = list_of_events.get('nextPageToken')
        if not page_token:
            break
    return event_list


def need_update(ics_event, google_event):
    if google_event['id'] == ''.join(ics_event.uid.split('-')[1:3]):
        return (ics_event.name != google_event.get('summary', None)
                or ics_event.location != google_event.get('location', None)
                or ics_event.description != google_event.get('description', None)
                or convert_to_RFC_datetime(ics_event.begin) != google_event['start'].get('dateTime', None)
                or convert_to_RFC_datetime(ics_event.end) != google_event['end'].get('dateTime', None))
    return False


def delete_all_events(service, back_off=1):
    try:
        page_token = None
        while True:
            list_of_events = service.events().list(
                calendarId=CALENDAR_ID, pageToken=page_token).execute()

            for event in list_of_events['items']:
                service.events().delete(calendarId=CALENDAR_ID,
                                        eventId=event['id']).execute()
            page_token = list_of_events.get('nextPageToken')
            if not page_token:
                break
    except:
        if back_off < MAX_BACKOFF:
            print('Warning : del')
            sleep(back_off)
            delete_all_events(service, 2 * back_off)


def add_event(service, ics_event, back_off=1):
    try:
        service.events().insert(calendarId=CALENDAR_ID,
                                body=ics_to_google_event(ics_event)).execute()
    except Exception as err:
        if err.status_code == 409:
            update_event(service, ics_event)
        else:
            if back_off < MAX_BACKOFF:
                print('Warning : add')
                sleep(back_off)
                add_event(service, ics_event, 2 * back_off)


def update_event(service, ics_event, back_off=1):
    try:
        service.events().update(calendarId=CALENDAR_ID, body=ics_to_google_event(
            ics_event), eventId=''.join(ics_event.uid.split('-')[1:3])).execute()
    except Exception:
        if back_off < MAX_BACKOFF:
            print('Warning : update')
            sleep(back_off)
            update_event(service, ics_event, 2 * back_off)


def delete_event(service, eventId, back_off=1):
    try:
        service.events().delete(calendarId=CALENDAR_ID, eventId=eventId).execute()
    except Exception:
        if back_off < MAX_BACKOFF:
            print('Warning : delete')
            sleep(back_off)
            delete_event(service, eventId, 2 * back_off)


def add_all_events(calendar, service):
    for event in calendar.timeline:
        add_event(service, event)


def add_new_events(service, google_calendar, ics_calendar):
    events_id = set()
    for e in google_calendar:
        events_id.add(e['id'])
    for event in ics_calendar.timeline:
        if ''.join(event.uid.split('-')[1:3]) not in events_id:
            add_event(service, event)
            print(event.name + ' has been added')


def delete_old_events(service, google_calendar, ics_calendar):
    events_id = set()
    for e in ics_calendar.timeline:
        events_id.add(''.join(e.uid.split('-')[1:3]))
    for event in google_calendar:
        if event['id'] not in events_id:
            delete_event(service, event['id'])
            print(event['summary'] + ' has been deleted')


def update_existing_events(service, ics_calendar):
    dico = {}
    google_calendar = get_google_calendar(service)
    for e in google_calendar:
        dico[e['id']] = e
    for i_event in ics_calendar.timeline:
        if need_update(i_event, dico[''.join(i_event.uid.split('-')[1:3])]):
            update_event(service, i_event)
            print(i_event.name + ' has been updated')

# OLD

# def main():
#     print('init')
#     filtered_calendar = get_filtered_calendar(URL_ICS, CURSUS)
#     service = Create_Service(
#         CLIENT_SECRET_FILE, API_SERVICE_NAME, API_VERSION, SCOPES)
#     delete_all_events(service)
#     add_all_events(filtered_calendar, service)
#     print('done')


def main():
    print('init')
    filtered_calendar = get_filtered_calendar(URL_ICS, CURSUS)
    service = Create_Service(
        CLIENT_SECRET_FILE, API_SERVICE_NAME, API_VERSION, SCOPES)
    google_calendar = get_google_calendar(service)
    add_new_events(service, google_calendar, filtered_calendar)
    delete_old_events(service, google_calendar, filtered_calendar)
    update_existing_events(service, filtered_calendar)
    print('done')


if __name__ == '__main__':
    t = 15
    print(f'Running every {t} minutes')
    main()
    schedule.every(t).minutes.do(main)
    while True:
        schedule.run_pending()
        sleep(1)
