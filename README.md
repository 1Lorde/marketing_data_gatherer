# marketing_data_gatherer

**marketing_data_gatherer** - includes script for gathering specific marketing data and Flask web application for demonstrating and management.

## Structure

**_bin/_** - data gathering module, which includes script for working with Binom and Push House APIs.

**_web/_** - demonstrating and management module, which includes Flask web application.

**_data/_** - includes database.

**_systemd/_** - systemd's services for daemonization.

## Run
1) Activate venv: `source venv/bin/activate`.
2) Run web app: `python3 web/run.py`.
3) Run script: `python3 bin/run.py`.
