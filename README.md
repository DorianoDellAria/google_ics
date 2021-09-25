# Google ics sync
python script for synchronising and filtering event from my cursus ics to Google calendar using Google API.
## Requirements
Install python requirements
```shell
pip install -r requirements.txt
```
Create a `.env` file and add these two variables:
```shell
CAL_ID=<Your google calendar id>
URL_ICS=<The URL to the ics>
```
Create a `creds.json` file and put your google's api key in it.