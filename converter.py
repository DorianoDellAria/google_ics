from ics import Event
from Google import convert_to_RFC_datetime


def event_to_dict(event: Event) -> dict:
    res = {}
    keys = ['name',
            'begin',
            'end',
            'duration',
            'uid',
            'description',
            'created',
            'last_modified',
            'location',
            'url',
            'transparent',
            'alarms',
            'attendees',
            'categories',
            'status',
            'organizer',
            'classification']
    for key in keys:
        res[key] = getattr(event, key)
        if isinstance(res[key], set):
            res[key] = list(res[key])
    return res


def ics_to_google_event(ics_event: Event) -> dict:
    dico = event_to_dict(ics_event)
    event = {}
    event['summary'] = dico['name']
    event['location'] = dico['location']
    event['description'] = dico['description']
    event['start'] = {
        'dateTime': convert_to_RFC_datetime(dico['begin']),
        'timeZone': 'Europe/Brussels',
    }
    event['end'] = {
        'dateTime': convert_to_RFC_datetime(dico['end']),
        'timeZone': 'Europe/Brussels',
    }
    event['id'] = ''.join(dico['uid'].split('-')[1:3])
    return event
