# Heating (relay) on/off control from a google calendar event
Steps to install from a fresh raspberry pi OS:
  1. Create a Raspberry pi image
     - set up wifi
     - enable ssh
     - setup a user that is not pi
  3. log into the raspberry pi with `ssh -X <user>@<raspberry-pi_ip_address>`
  6. Clone this repository
  5. create and activate a python virtual enviroment:
     - `python -m venv /home/<user>/PYTHON/venv`
     - `source ~/PYTHON/venv/bin/activate`
  1. Update and install requirements:
     - `pip install --upgrade requests`
     - `pip install -r requirements.txt`
  1. Make sure the user is part of the GPIO group
     -`sudo adduser tim gpio`
  1. Test the GPIO controls the relay
     -`cd ~/PYTHON/heating`
     -`python relay -h` to get what raspberry pi pins might be connected to what relay and general relay.py usage
     -`python relay -r 4 -p 1` to turn on relay connected to pin 4
  3. Create a new google calendar
  4. Share the calendar with people who will need access
  5. copy calendar ID
  6. Run the python heating script for the first time to do first time run setup stuff.
     - `cd ~/PYTHON/heating`
     - `python heating.py -s .relay_1_settings.json` change the settings file name to decribe what it's controlling. this is stored in your home folder as a hidden file
     - you will be asked for the calendar ID - paste it here
     - you will be asked for the relay number
     - 

