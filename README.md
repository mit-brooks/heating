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
     - on the absolute first run, you will be asked to click on a link to authenticate. hence ssh -X ...
     - log in to your google account
     - I've not submitted this app to be vetted by google so you will have to click advanced, then go to heating (unsafe)
      I promise - it's as safe as I can think of... 
![yes_I_Know_ive_not_been_google_vetted](https://github.com/mit-brooks/heating/assets/14214699/5121a92a-a17f-45ef-be67-8fb7e5af9a41)
     - click "allow" to authorise the script to access this calendar 
![image](https://github.com/mit-brooks/heating/assets/14214699/4c407877-5b44-4dae-8652-1f1cb021da85)
     - you will be asked for the calendar ID - paste it here and press enter
     - you will be asked for the relay number - enter it and press enter
  1. Test the relay by setting an event happening now in the calendar
  2. run the python script - it should detect the event and turn on the relay
     ```
     python heating.py -s .relay_2_settings.json
     Setting up query: 2023-08-18T08:27:42.634531+01:00 to 2023-08-25T09:01:42.950799+01:00 modified after 2023-08-18 09:01:42.950799+01:00
     Setting up query: 2023-08-25T09:01:42.950799+01:00 to 2023-08-25T09:27:42.634531+01:00 modified after None
     Submitting query
     Query results received
     on
     turned relay 27 on at  2023-08-18 09:27:43.409294+01:00
     Sync succeeded
     ```
  2. Delete the calendar event and run the script again and the relay will turn off :-)
  3. Now add a line to your crontab to run the script every minute
     - `crontab -e`
     - add a line similar to the following, changing the name of the settings file for each file
       ```
       */1 *  *   *   *     /usr/bin/env bash -c 'cd /home/tim/PYTHON/heating && source /home/tim/PYTHON/venv/bin/activate && ./heating.py -s .relay_1_settings.json' > /dev/null 2&1
       */1 *  *   *   *     /usr/bin/env bash -c 'cd /home/tim/PYTHON/heating && source /home/tim/PYTHON/venv/bin/activate && ./heating.py -s .relay_2_settings.json' > /dev/null 2&1
       ```
     - close cron, test once more that adding a calendar event triggers the relay (now without running the script manually)
You are done!

