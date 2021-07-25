import json, os, requests, sys, logging
from pathlib import Path

from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import ClientContext

print("""
 _______________________________________________________
|\                                                      \ 
| \______________________________________________________\ 
| |    _____ __             __    ____        _       __  |
| |   / ___// /_____ ______/ /_  / __ \____  (_)___  / /_ |
| |   \__ \/ __/ __ `/ ___/ __ \/ /_/ / __ \/ / __ \/ __/ |
| |  ___/ / /_/ /_/ (__  ) / / / ____/ /_/ / / / / / /_   |
\ | /____/\__/\__,_/____/_/ /_/_/    \____/_/_/ /_/\__/   |
 \|_______________________________________________________| 
""")



# Provision env file
if "--create-env" in sys.argv:
    TemplateFile = "HEALTHCHECK_URL=\n" + \
        "SENTRY_DSN=\n" + \
        "SENTRY_SAMPLE_RATE=\n" + \
        "LOCAL_PATH=\n" + \
        "REMOTE_USERNAME=\n" + \
        "REMOTE_PASSWORD=\n" + \
        "REMOTE_URL=\n" + \
        "SHAREPOINT_SUBSITE_PATH=\n" + \
        "SHAREPOINT_DOCUMENT_LIBRARY=\n" + \
        "SHAREPOINT_DESTINATION_FOLDER=\n"
    with open(".env", mode="w") as envFile:
        envFile.write(TemplateFile)

    print("Generated .env from template")
    sys.exit()

logging.basicConfig(filename=os.path.join(os.path.dirname(os.path.realpath(__file__)), "stashpoint.log"), level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logging.info("Starting up StashPoint!")
logging.info("Configuring Environment")

from dotenv import load_dotenv
load_dotenv()

if os.getenv("SENTRY_DSN"):
    import sentry_sdk
    sentry_sdk.init(
        os.getenv("SENTRY_DSN"),

        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=os.getenv("SENTRY_SAMPLE_RATE")
    )
    logging.info("Loaded Sentry")

settings = {
    'localFolder': os.environ["LOCAL_PATH"],
    'user_credentials': {
        'username': os.environ["REMOTE_USERNAME"],
        'password': os.environ["REMOTE_PASSWORD"],
    },
    'url': os.environ["REMOTE_URL"],
    'subsitePath': os.environ["SHAREPOINT_SUBSITE_PATH"],
    'documentLibrary': os.environ["SHAREPOINT_DOCUMENT_LIBRARY"],
    'destinationFolder': os.environ["SHAREPOINT_DESTINATION_FOLDER"],
    'chunkSize': os.getenv("UPLOAD_CHUNK_SIZE", 1000000)
}


if os.getenv("HEALTHCHECK_URL"):
    try:
        requests.get(os.getenv("HEALTHCHECK_URL") + "/start", timeout=5)
        logging.info("Informed Healthcheck that we have started")
    except requests.exceptions.RequestException:
        # If the network request fails for any reason, we don't want
        # it to prevent the main job from running
        logging.error("Failed to contact Healthcheck job start endpoint!")


localPath = Path(settings["localFolder"])
dirs = [x for x in localPath.rglob("*") if x.is_dir()]
files = [x for x in localPath.rglob("*") if x.is_file()]


success = True
try:
    ctx_auth = AuthenticationContext(url=settings['url'])
    if ctx_auth.acquire_token_for_user(username=settings['user_credentials']['username'],
                                       password=settings['user_credentials']['password']):
        logging.info("Logged in to Office 365")
        ctx = ClientContext(f"{settings['url']}/{settings['subsitePath']}", ctx_auth)
        # Create folders if they don't exist
        for name in dirs:
            p = '/'.join(filter(lambda x: x not in localPath.parts, name.parts))
            folder = f'/{settings["documentLibrary"]}/{settings["destinationFolder"]}/{p}'
            ctx.web.ensure_folder_path(folder).execute_query()
        
        # Upload files
        for name in files:
            logging.info("Uploading {0}".format(name))
            path = str(name.absolute())
            upload_folder = '/'.join(filter(lambda x: x not in localPath.parts, name.parent.parts))
            target_path = f'/{settings["documentLibrary"]}/{settings["destinationFolder"]}/{upload_folder}'
            if settings["subsitePath"]:
                target_path = "/"+settings["subsitePath"]+target_path
            target_folder = ctx.web.get_folder_by_server_relative_url(
                target_path
            )
            file_size = os.path.getsize(path)
            uploaded_file = target_folder.files.create_upload_session(
                path,
                settings["chunkSize"],
                lambda offset: print("Uploaded {0} bytes of {1} total...[{2}%]".format(offset, file_size, round(offset / file_size * 100, 2)), end="\r")
            ).execute_query()
            print('File {0} has been uploaded successfully'.format(uploaded_file.serverRelativeUrl))
            logging.info('File {0} has been uploaded successfully'.format(uploaded_file.serverRelativeUrl))

except Exception as e:
    logging.exception("StashPoint Failed!")
    if os.getenv("SENTRY_DSN"):
        sentry_sdk.capture_exception(e)
    success = False

if os.getenv("HEALTHCHECK_URL"):
    requests.get(os.getenv("HEALTHCHECK_URL") if success else os.getenv("HEALTHCHECK_URL") + "/fail")
    logging.info("Reported job status to Healthcheck")

logging.info("Finished!")

