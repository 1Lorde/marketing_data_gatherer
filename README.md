# Marketing Data Gatherer
![banner](https://raw.githubusercontent.com/1Lorde/marketing_data_gatherer/dev/img/stats.png)

**marketing_data_gatherer** - project, which consists of script for gathering specific marketing data and Flask web application for demonstrate and manage this data. Also user can set rules for starting or pausing specific campaigns, when condition is true.

## Structure

**_gatherer/_** - resources for data gathering.

**_web/_** - resources for demonstrating and management Flask web application.

**_utils/_** - utilities for working with Binom and Push House APIs.

**_models/_** - includes db models.

**_data/_** - includes database.

**_systemd/_** - systemd's services for daemonization.

## Build
1) Create venv: `virtualenv venv`.
2) Activate venv: `source venv/bin/activate`.
3) Install requirements: `pip install -r requirements.txt`.

## Run
1) Activate venv: `source venv/bin/activate`.
2) Run web app: `python3 run_web.py`.
3) Run script: `python3 run_gatherer.py`.

## Screenshots
![screenshot_1](https://raw.githubusercontent.com/1Lorde/marketing_data_gatherer/dev/img/binoms.png)
![screenshot_2](https://raw.githubusercontent.com/1Lorde/marketing_data_gatherer/dev/img/add_rule.png)
![screenshot_3](https://raw.githubusercontent.com/1Lorde/marketing_data_gatherer/dev/img/rules_list.png)
