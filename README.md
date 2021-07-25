```
 _______________________________________________________
|\                                                      \ 
| \______________________________________________________\ 
| |    _____ __             __    ____        _       __  |
| |   / ___// /_____ ______/ /_  / __ \____  (_)___  / /_ |
| |   \__ \/ __/ __ `/ ___/ __ \/ /_/ / __ \/ / __ \/ __/ |
| |  ___/ / /_/ /_/ (__  ) / / / ____/ /_/ / / / / / /_   |
\ | /____/\__/\__,_/____/_/ /_/_/    \____/_/_/ /_/\__/   |
 \|_______________________________________________________| 
```

A python script to upload a folder to a SharePoint document library.

## Usage

StashPoint is built to be called from a job scheduler like cron. After configuring a .env file next to the script, run it with python and it will upload the folder.

## Setup

### Environment Prep

First clone the repo, then stand up the venv:

```shell
cd stashpoint
python -m pip install pipenv
pipenv install
```

### Application Configuration

You must create an env file to setup StashPoint, it will not run without it. Below is an example env file:

```env
HEALTHCHECK_URL=HEALTHCHECK URL
SENTRY_DSN=SENTRY DSN
SENTRY_SAMPLE_RATE=0.2

LOCAL_PATH=./TEST
REMOTE_USERNAME=USERNAME
REMOTE_PASSWORD=PASSWORD
REMOTE_PATH=Documents
REMOTE_URL=https://[sharepoint instance].sharepoint.com/test-department
```

You can create a template quickly by calling `python main.py --create-env` from the project directory.

Variable | Description
---------|------------
HEALTHCHECK_URL | URL Healthcheck will use to phone home. This script will check in at the start and end of a run.
SENTRY_DSN | Sentry Project DSN for error reporting
SENTRY_SAMPLE_RATE | Error sample rate for sentry
LOCAL_PATH | Local directory to upload contents
REMOTE_USERNAME | Office365 Username. User must have access to upload destination
REMOTE_PASSWORD | Office365 Password
REMOTE_PATH | Relative path to the folder the files will be uploaded to. For example, `/sites/team/Shared Documents` or `/test-department/Shared Documents/TestFolder`
REMOTE_URL | URL of target sharepoint site. This can be a group or subsite as well.