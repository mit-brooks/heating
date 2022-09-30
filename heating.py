#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    gcalcron v2.1
#
#    Copyright Fabrice Bernhard 2011-2013
#    fabriceb@theodo.fr
#    www.theodo.fr

"""Command-line synchronisation application between Google Calendar and Linux's Crontab.
Usage:
  $ python gcalcron2.py
"""

# Google API
import argparse
import httplib2
import os
import sys
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from relay import relay

# GCalCron
import json
import datetime
from datetime import timezone
import dateutil.parser
from dateutil.tz import gettz
import time
import subprocess
import re
import logging

logger = logging.getLogger(__name__)

# Parser for command-line arguments.
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    )
parser.add_argument('--reset', default=False,
                    help='Reset all synchronised events')
parser.add_argument('-s', '--settings_file', default='.heating',
                    help='Name of settings file in home folder. change this for multiple instances')

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


class GCalAdapter:
    """
    Adapter class which communicates with the Google Calendar API
    @since 2011-06-19
    """

    # CLIENT_SECRETS is name of a file containing the OAuth 2.0 information for this
    # application, including client_id and client_secret. You can see the Client ID
    # and Client secret on the APIs page in the Cloud Console:
    # <https://cloud.google.com/console#/project/395452703880/apiui>
    CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), 'client_secrets.json')

    def __init__(self, calendarId=None, flags=None):
        self.calendarId = calendarId
        self.service = None
        self.flags = flags
        self.creds = None
        if os.path.exists('token.json'):
            self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    @staticmethod
    def _assure_refreshed(credentials: Credentials):
        if not credentials.valid and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        return credentials

    def get_service(self):

        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self._assure_refreshed(self.creds)
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'client_secrets.json', SCOPES)
                self.creds = flow.run_local_server(host='localhost', port=8080)
                # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(self.creds.to_json())

        try:
            self.service = build('calendar', 'v3', credentials=self.creds)
        except HttpError as error:
            print("An Error occured: %s" % error)

        return self.service

    def get_query(self, start_min, start_max, updated_min=None):
        """
    Builds the Google Calendar query with default options set

    >>> g = GCalAdapter()
    >>> g.get_query(datetime.datetime(2011, 6, 19, 14, 0), datetime.datetime(2011, 6, 26, 14, 0), datetime.datetime(2011, 6, 18, 14, 0))
    {'orderBy': 'updated', 'showDeleted': True, 'calendarId': None, 'timeMin': '2011-06-19T14:00:00', 'updatedMin': '2011-06-18T14:00:00', 'timeMax': '2011-06-26T14:00:00', 'fields': 'items(description,end,id,start,status,summary,updated)', 'singleEvents': True, 'maxResults': 1000}

    @author Fabrice Bernhard
    @since 2011-06-19
    """

        logger.info('Setting up query: %s to %s modified after %s' % (
        start_min.isoformat(), start_max.isoformat(), updated_min))

        query = {
            'calendarId': self.calendarId,
            'maxResults': 1000,
            'orderBy': 'updated',
            'showDeleted': True,
            'singleEvents': True,
            'fields': 'items(description,end,id,start,status,summary,updated)',
            'timeMin': start_min.isoformat(),
            'timeMax': start_max.isoformat(),
        }

        if updated_min:
            query['updatedMin'] = updated_min.isoformat()

        return query

    def queryApi(self, queries):
        """Query the Google Calendar API."""

        logger.info('Submitting query')

        entries = []
        for query in queries:
            pageToken = None
            while True:
                query['pageToken'] = pageToken
                gCalEvents = self.get_service().events().list(**query).execute()
                entries += gCalEvents['items']
                pageToken = gCalEvents.get('nextPageToken')
                if not pageToken:
                    break

        logger.info('Query results received')
        logger.debug(entries)

        return entries

    def get_events(self, sync_start, last_sync=None, num_days=datetime.timedelta(days=7)):
        """
    Gets a list of events to sync
     - events between sync_start and last_sync + num_days which have been updated since last_sync
     - new events between last_sync + num_days and sync_start + num_days
    @author Fabrice Bernhard
    @since 2011-06-13
    """

        queries = []
        end = sync_start + num_days
        if last_sync:
            # query all events modified since last synchronisation
            queries.append(self.get_query(sync_start - datetime.timedelta(hours=1), last_sync + num_days, last_sync))
            # query all events which appeared in the [last_sync + num_days, sync_start + num_days] time frame
            queries.append(self.get_query(last_sync + num_days,
                                          end))  # TODO: only do this every few hours... log gets filled with updates, job numbers keep incrementing
        else:
            queries.append(self.get_query(sync_start, end))

        return self.queryApi(queries)


class GCalCron:
    """
  Schedule your cron commands in a dedicated Google Calendar,
  this class will convert them into UNIX "at" job list and keep
  them synchronised in case of updates

  @author Fabrice Bernhard
  @since 2011-06-13
  """

    settings = None

    def __init__(self, gCalAdapter=None, flags=None, settings=None):
        if settings:
            self.settings = json.load(settings)
        else:
            if flags:
                self.settings_file = os.getenv('HOME') + '/' + flags.settings_file
            else:
                self.settings_file = os.getenv('HOME') + '/' + '.gcalcron2'
            self.load_settings()
        self.gCalAdapter = gCalAdapter

    def load_settings(self):
        try:
            with open(self.settings_file) as f:
                self.settings = json.load(f)
        except IOError:
            calendarId = input(
                'Calendar id (in the form of XXXXX....XXXX@group.calendar.google.com or for the main one just your Google email): ')
            relay_pin = int(input(
                'which pin is the relay you want to control connected to eg: "1" for back hall, "2" for main hall (24 = a and 25 = b for slice of relay)'))
            self.init_settings(calendarId, relay_pin)
            self.save_settings()

    def save_settings(self):
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=2)

    def init_settings(self, calendarId,
                      relay_pin):
        self.settings = {
            "events": [],
            "calendarId": calendarId,
            "relay_pin": relay_pin,  # the pin that the relay is controlled by
            "last_sync": None
        }

    def getCalendarId(self):
        return self.settings["calendarId"]

    def reset_settings(self):
        self.settings['last_sync'] = None
        self.settings['events'] = []
        self.save_settings()

    def sync_gcal_to_cron(self, num_days=datetime.timedelta(days=7), verbose=True):
        """
    - fetches a list events through the GoogleCalendar adapter
    - merge new events with the local events in the settings file
    - decided if relay should be on or off

    @author Tim Brooks
    @since 2014-12-01
    """

        last_sync = None
        # if we have recorded the last time we sync'ed
        if self.settings['last_sync']:
            temp = dateutil.parser.parse(self.settings['last_sync'])
            # and the last time was more than num_days ago (because that would only get events in the past...)
            if temp - datetime.timedelta(days=0) > datetime.datetime.now(gettz()) - num_days:
                last_sync = temp

        sync_start = datetime.datetime.now(gettz())

        # get new and updated events (if connected to the internet)
        new_events = None
        try:
            new_events = self.gCalAdapter.get_events(sync_start, last_sync, num_days)
        except httplib2.ServerNotFoundError:
            logger.error('server not found - not updating local events')

        # merge them to locally saved
        local_events = self.settings['events']
        events = merge_events(local_events, new_events)

        # update the relay position
        update_relay(self.settings['relay_pin'], events, datetime.datetime.now(gettz()))

        events = prune_old_events(events, datetime.datetime.now(gettz()))

        self.settings['last_sync'] = str(sync_start)
        self.settings['events'] = events
        self.save_settings()


def merge_events(local_events=[], new_events=None):
    """
  merges new and updated events to the locally saved events.
  >>> le = []
  >>> ne = [{u'description': u'description 1', u'id': u'1'}]
  >>> le = merge_events(le, ne)
  >>> le
  [{u'description': u'description 1', u'id': u'1'}]
  >>> ne = [{u'description': u'new description 1', u'id': u'1'}]
  >>> le = merge_events(le, ne)
  >>> le
  [{u'description': u'new description 1', u'id': u'1'}]
  >>> ne = [{u'description': u'description 2', u'id': u'2'}]
  >>> le = merge_events(le, ne)
  >>> le
  [{u'description': u'new description 1', u'id': u'1'}, {u'description': u'description 2', u'id': u'2'}]
  """
    if new_events:
        for index, event in enumerate(new_events):  # enumerate?
            # for each new event, if eventid is in local calendar, replace that event
            matched_local_event = next((le for le in local_events if le[u'id'] == event[u'id']), None)
            if matched_local_event:
                # event index?
                local_events[local_events.index(matched_local_event)] = event
            else:
                local_events.append(event)
    return local_events


def update_relay(pin, events, now):
    """switch relay position to closed if there is currently an event. If not, open the relay
  
  Arguments:
  - `pin`: pin that the relay is connected too
  - `events`: list of google calendar events (json)
  - `now`: date time now

  >>> pin = 1
  >>> events = ([{u'status': u'confirmed', u'updated': u'2013-12-22T19:49:13.750Z', u'end': {u'dateTime': u'2014-12-07T22:00:00+01:00'}, u'description': u'', u'summary': u'heat', u'start': {u'dateTime': u'2014-12-07T21:00:00+01:00'}, u'id': u'olbia2urfm1ns0h88v4u0d9a5g'}])
  >>> now = datetime.datetime(2014, 12, 7, 21, 25, 52, 93975)
  >>> update_relay(pin, events, now)
  1
  >>> relay(pin = pin, position = 0)
  0
  >>> events = ([{u'status': u'cancelled', u'updated': u'2013-12-22T19:49:13.750Z', u'end': {u'dateTime': u'2014-12-07T22:00:00+01:00'}, u'description': u'', u'summary': u'heat', u'start': {u'dateTime': u'2014-12-07T21:00:00+01:00'}, u'id': u'olbia2urfm1ns0h88v4u0d9a52g'}])
  >>> update_relay(pin, events, now)
  0
  >>> events = ([{u'status': u'confirmed', u'updated': u'2013-12-22T19:49:13.750Z', u'end': {u'dateTime': u'2114-12-07T22:00:00+01:00'}, u'description': u'', u'summary': u'heat', u'start': {u'dateTime': u'2114-12-07T21:00:00+01:00'}, u'id': u'olbia2urfm1ns0h88v4u0d9a5g'}, {u'status': u'confirmed', u'updated': u'2013-12-22T19:49:13.750Z', u'end': {u'dateTime': u'2013-12-07T22:00:00+01:00'}, u'description': u'', u'summary': u'heat', u'start': {u'dateTime': u'2013-12-07T21:00:00+01:00'}, u'id': u'olbia2urfm1ns0h88v4u0d9a5g'}])
  >>> update_relay(pin, events, now)
  0
  """
    # print('now:', now)
    # read current relay position
    relay_pos = relay(pin=pin)
    set_relay = 0  # default is to set relay off
    for event in events:  # for each event
        start_time = dateutil.parser.parse(event['start']['dateTime']).replace(tzinfo=None)
        # print(start_time)
        end_time = dateutil.parser.parse(event['end']['dateTime']).replace(tzinfo=None)
        # print(end_time)
        # print(event['status'])
        logger.debug(event['status'])
        if (event[u'status'] != u'cancelled'):  # if the event hasn't been canceled
            if start_time < now < end_time:  # and the event is currently occuring
                set_relay = 1  # turn relay on
                # print('relay should be on')
                break  # no need to look further

    relay(pin=pin, position=set_relay)  # set new relay position
    if (relay_pos != set_relay):
        if relay(pin=pin) == 1:
            logger.info('turned relay {0} on at  {1}'.format(pin, now))
            # print('turned relay {0} on at  {1}'.format(pin, now))
            # return 1
        else:
            logger.info('turned relay {0} off at  {1}'.format(pin, now))
            # print('turned relay {0} off at {1}'.format(pin, now))
            # return 0
    return relay(pin=pin)


def prune_old_events(events, now):
    """ remove events that are in the past
  
  Arguments:
  - `events`: list of json events
  - `now`: datetime now
  
  >>> events = ([{u'status': u'confirmed', u'updated': u'2013-12-22T19:49:13.750Z', u'end': {u'dateTime': u'2114-12-07T22:00:00+01:00'}, u'description': u'', u'summary': u'heat', u'start': {u'dateTime': u'2114-12-07T21:00:00+01:00'}, u'id': u'olbia2urfm1ns0h88v4u0d9a5g'}, {u'status': u'confirmed', u'updated': u'2013-12-22T19:49:13.750Z', u'end': {u'dateTime': u'2013-12-07T22:00:00+01:00'}, u'description': u'', u'summary': u'heat', u'start': {u'dateTime': u'2013-12-07T21:00:00+01:00'}, u'id': u'olbia2urfm1ns0h88v4u0d9a5g'}])
  >>> now = datetime.datetime(2014, 12, 7, 21, 36, 35, 63970)
  >>> prune_old_events(events, now)
  [{u'status': u'confirmed', u'updated': u'2013-12-22T19:49:13.750Z', u'end': {u'dateTime': u'2114-12-07T22:00:00+01:00'}, u'description': u'', u'summary': u'heat', u'start': {u'dateTime': u'2114-12-07T21:00:00+01:00'}, u'id': u'olbia2urfm1ns0h88v4u0d9a5g'}]
  """
    for event in events:  # for each event
        end_time = dateutil.parser.parse(event['end']['dateTime']).replace(tzinfo=None)
        if end_time < now:  # and the event is currently occuring
            logger.info('removing event {0}: in the past'.format(event[u'id']))
            events.remove(event)
    return events


def main(argv):
    # Parse the command-line flags.
    flags = parser.parse_args(argv[1:])

    logger.setLevel(logging.INFO)
    h1 = logging.StreamHandler(sys.stdout)
    logger.addHandler(h1)

    fh = logging.FileHandler(os.path.join(os.path.dirname(__file__), 'heating.log'))
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)

    try:
        g = GCalCron(flags=flags)
        gCalAdapter = GCalAdapter(g.getCalendarId(), flags)
        g.gCalAdapter = gCalAdapter

        if flags.reset:
            g.reset_settings()
        else:
            g.sync_gcal_to_cron()
            logger.info('Sync succeeded')
    except:
        logging.exception('Sync failed')


if __name__ == '__main__':
    main(sys.argv)
