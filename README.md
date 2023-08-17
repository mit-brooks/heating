# Heating (relay) on/off control from a google calendar event
Steps to install from a fresh raspberry pi OS:
  1. Create a Raspberry pi image
     - set up wifi
     - enable ssh
     - setup a user that is not pi
  3. Clone this repository
  4. create and activate a python virtual enviroment:
     - `python -m venv /home/user/PYTHON/venv`
     - `source venv/bin/activate`
  1. Update and install requirements:
     - `pip install --upgrade requests`
     - `pip install -r requirements.txt`
  1. Make sure the user is part of the GPIO group
     -`sudo adduser tim gpio`
  1.
  2. Create a new google calendar
  3. Share the calendar with people who will need access
  4. copy calendar ID
