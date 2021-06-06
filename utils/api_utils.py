import json
import logging
import time
from datetime import datetime, timedelta

import requests
from requests import HTTPError
from sqlalchemy.sql.expression import and_

from models.models import Campaign, Source, DailyCampaign, CampaignRule, DailySource, SourceRule, db, PausedSource, \
    PausedCampaign
from utils.rules_utils import get_comparison_operator, get_campaign_action, get_source_action


class ApiUtils:
    def __init__(self, config):
        self.config = config

    def get_binom_campaigns_url(self, ts_id, start_date=None, end_date=None):
        if int(ts_id) == self.config['traffic_source_ids']['push_house']:
            campaigns_url = self.config['binom_urls']['ph_campaigns']
        else:
            campaigns_url = self.config['binom_urls']['ungads_campaigns']

        if start_date and end_date:
            start_date = start_date.strftime("%Y-%m-%d")
            end_date = end_date.strftime("%Y-%m-%d")

            campaigns_url = campaigns_url.replace('[DATE_S]', start_date)
            campaigns_url = campaigns_url.replace('[DATE_E]', end_date)
        else:
            current_date = datetime.now().strftime("%Y-%m-%d")
            campaigns_url = campaigns_url.replace('[DATE_S]', current_date)
            campaigns_url = campaigns_url.replace('[DATE_E]', current_date)

        binom_api_key = self.config["api_keys"]["binom"]
        campaigns_url = f'{campaigns_url}&api_key={binom_api_key}'

        return campaigns_url

    def get_push_house_campaign_url(self, campaign_name, start_date=None, end_date=None):
        stats_url = self.config['push_house_urls']['stats']
        push_house_api_key = self.config["api_keys"]["push_house"]

        if start_date and end_date:
            start_date = start_date.strftime("%Y-%m-%d")
            end_date = end_date.strftime("%Y-%m-%d")

            stats_url = f'{stats_url}{push_house_api_key}/date/{start_date}/{end_date}/{campaign_name}'
        else:
            current_date = datetime.now().strftime("%Y-%m-%d")
            stats_url = f'{stats_url}{push_house_api_key}/date/{current_date}/{current_date}/{campaign_name}'

        return stats_url

    def get_ungads_campaign_url(self, campaign_name, start_date=None, end_date=None):
        stats_url = self.config['ungads_urls']['stats']
        ungads_api_key = self.config["api_keys"]["ungads"]
        stats_url = stats_url.replace('[API_KEY]', ungads_api_key)

        if start_date and end_date:
            start_date = start_date.strftime("%Y-%m-%d")
            end_date = end_date.strftime("%Y-%m-%d")

            stats_url = f'{stats_url}?date_start={start_date}&date_finish={end_date}&campaign_id={campaign_name}'
        else:
            stats_url = f'{stats_url}?campaign_id={campaign_name}'

        return stats_url

    def get_binom_sources_url(self, ts_id, start_date=None, end_date=None):
        if int(ts_id) == self.config['traffic_source_ids']['push_house']:
            sources_url = self.config['binom_urls']['ph_sources']
        else:
            sources_url = self.config['binom_urls']['ungads_sources']

        if start_date and end_date:
            start_date = start_date.strftime("%Y-%m-%d")
            end_date = end_date.strftime("%Y-%m-%d")

            sources_url = sources_url.replace('[DATE_S]', start_date)
            sources_url = sources_url.replace('[DATE_E]', end_date)
        else:
            current_date = datetime.now().strftime("%Y-%m-%d")
            sources_url = sources_url.replace('[DATE_S]', current_date)
            sources_url = sources_url.replace('[DATE_E]', current_date)

        binom_api_key = self.config["api_keys"]["binom"]
        sources_url = f'{sources_url}&api_key={binom_api_key}'

        return sources_url

    def get_push_house_sources_url(self, campaign_name, start_date=None, end_date=None):
        stats_url = self.config['push_house_urls']['stats']
        push_house_api_key = self.config["api_keys"]["push_house"]

        if start_date and end_date:
            start_date = start_date.strftime("%Y-%m-%d")
            end_date = end_date.strftime("%Y-%m-%d")

            stats_url = f'{stats_url}{push_house_api_key}/subacc/{start_date}/{end_date}/{campaign_name}'
        else:
            current_date = datetime.now().strftime("%Y-%m-%d")
            stats_url = f'{stats_url}{push_house_api_key}/subacc/{current_date}/{current_date}/{campaign_name}'

        return stats_url

    def get_ungads_publishers_url(self, campaign_name, start_date=None, end_date=None):
        stats_url = self.config['ungads_urls']['stats']
        ungads_api_key = self.config["api_keys"]["ungads"]
        stats_url = stats_url.replace('[API_KEY]', ungads_api_key)

        if start_date and end_date:
            start_date = start_date.strftime("%Y-%m-%d")
            end_date = end_date.strftime("%Y-%m-%d")

            stats_url = f'{stats_url}?group_by[]=publisher&group_by[]=date&date_start={start_date}&date_finish={end_date}&campaign_id={campaign_name}'
        else:
            stats_url = f'{stats_url}?group_by[]=publisher&group_by[]=date&campaign_id={campaign_name}'

        return stats_url

    def get_campaign_status_url(self):
        status_url = self.config['ungads_urls']['campaign_status']
        ungads_api_key = self.config["api_keys"]["ungads"]
        status_url = status_url.replace('[API_KEY]', ungads_api_key)
        return status_url

    def parse_binom_campaigns_json(self, json, ts_id):
        campaigns = []
        if not json:
            return campaigns

        if json != 'no_clicks':
            for element in json:
                try:
                    if 'name' not in element:
                        continue

                    name = element['name']

                    if not name.isnumeric():
                        continue

                    revenue = float(element['revenue'])
                    campaign = Campaign(name, revenue, ts_id)
                    campaign.binom_clicks = int(element['clicks'])
                    campaign.lp_clicks = int(element['lp_clicks'])
                    campaign.leads = int(element['leads'])
                    if campaign.leads != 0:
                        campaign.payout = campaign.revenue / campaign.leads
                    campaigns.append(campaign)
                except:
                    logging.error('Parsing campaigns json error')

        return campaigns

    def parse_ts_campaign_json(self, campaign, json):
        if not json:
            return campaign

        if int(campaign.traffic_source) == self.config['traffic_source_ids']['push_house']:
            campaign.clicks = float(json[0]['clicks'])
            campaign.impressions = float(json[0]['shows'])
            campaign.cost = float(json[0]['cost'])
        else:
            campaign.clicks = float(json[0]['clicks'])
            campaign.impressions = float(json[0]['impressions'])
            campaign.cost = float(json[0]['spent_advertiser'])

        campaign.profit = campaign.revenue - campaign.cost

        if campaign.clicks != 0:
            campaign.cpc = campaign.cost / campaign.clicks
            campaign.epc = campaign.revenue / campaign.clicks

        if campaign.binom_clicks != 0:
            campaign.lp_ctr = campaign.lp_clicks / campaign.binom_clicks * 100

        if campaign.cost != 0:
            campaign.roi = campaign.profit / campaign.cost * 100

        if campaign.impressions != 0:
            campaign.ctr = campaign.clicks / campaign.impressions * 100
            campaign.cpm = campaign.cost / campaign.impressions * 1000

        return campaign

    def parse_campaign_status_json(self, ts_id, json):
        if not json or int(ts_id) == self.config['traffic_source_ids']['push_house']:
            return 'undefined'

        return json[next(iter(json))]['status']

    def parse_binom_sources_json(self, json, ts_id):
        sources = []
        campaign_name = ''

        if not json:
            return sources

        if json != 'no_clicks':
            for element in json:
                try:
                    if element['level'] == '1':
                        campaign_name = element['name']
                        continue

                    if not campaign_name.isnumeric():
                        continue

                    name = element['name']
                    revenue = float(element['revenue'])
                    source = Source(name, campaign_name, revenue, ts_id)
                    source.binom_clicks = int(element['clicks'])
                    source.lp_clicks = int(element['lp_clicks'])
                    source.leads = int(element['leads'])
                    if source.leads != 0:
                        source.payout = source.revenue / source.leads
                    sources.append(source)
                except Exception as e:
                    logging.error('Parsing sources json error ' + str(e))

        return sources

    def parse_ts_sources_json(self, campaign_name, sources, ts_id, json):
        if not json:
            return sources

        sources_with_campaign_name = set()
        [sources_with_campaign_name.add(source) for source in sources if source.campaign_name == campaign_name]

        sources_names = set((source.name for source in sources_with_campaign_name))

        filtered_json = []
        if 'tname' in str(json):
            [filtered_json.append(element) for element in json if str(element['tname']) in sources_names]

            for element in filtered_json:
                for source in sources_with_campaign_name:
                    if str(element['tname']) == source.name:
                        source.clicks = float(element['clicks'])
                        source.impressions = float(element['shows'])
                        source.cost = float(element['cost'])

                        source.profit = source.revenue - source.cost

                        if source.clicks != 0:
                            source.cpc = source.cost / source.clicks
                            source.epc = source.revenue / source.clicks

                        if source.binom_clicks != 0:
                            source.lp_ctr = source.lp_clicks / source.binom_clicks * 100

                        if source.cost != 0:
                            source.roi = source.profit / source.cost * 100

                        if source.impressions != 0:
                            source.ctr = source.clicks / source.impressions * 100
                            source.cpm = source.cost / source.impressions * 1000

        elif 'publisher_id' in str(json):
            [filtered_json.append(element) for element in json if str(element['publisher_id']) in sources_names]

            for element in filtered_json:
                for source in sources_with_campaign_name:
                    if str(element['publisher_id']) == source.name:
                        source.clicks = float(element['clicks'])
                        source.impressions = float(element['impressions'])
                        source.cost = float(element['spent_advertiser'])

                        source.profit = source.revenue - source.cost

                        if source.clicks != 0:
                            source.cpc = source.cost / source.clicks
                            source.epc = source.revenue / source.clicks

                        if source.binom_clicks != 0:
                            source.lp_ctr = source.lp_clicks / source.binom_clicks * 100

                        if source.cost != 0:
                            source.roi = source.profit / source.cost * 100

                        if source.impressions != 0:
                            source.ctr = source.clicks / source.impressions * 100
                            source.cpm = source.cost / source.impressions * 1000

        return list(sources_with_campaign_name)

    def get_campaigns_data_from_binom(self, ts_id, start_date=None, end_date=None):
        try:
            if start_date and end_date:
                url = self.get_binom_campaigns_url(ts_id, start_date, end_date)
            else:
                url = self.get_binom_campaigns_url(ts_id)

            response_json = None
            while not response_json or 'Exception' in str(response_json):
                response = requests.get(url)
                if response.text == 'null':
                    break
                response_json = response.json()
                logging.debug(f"{str(response_json)[0:300]}... (output suppressed)")
                time.sleep(3)

            # If the response was successful, no Exception will be raised
            response.raise_for_status()
        except HTTPError as http_err:
            logging.error(f'HTTP error occurred: {http_err}')  # Python 3.6
        except Exception as err:
            logging.error(f'Other error occurred: {err}')  # Python 3.6
        else:
            logging.debug(f'Fetched campaigns data from binom (ts={ts_id})')
            return self.parse_binom_campaigns_json(response.json(), ts_id)

    def get_campaigns_data_from_ts(self, campaigns, ts_id, start_date=None, end_date=None):
        for campaign in campaigns:
            try:
                if int(ts_id) == self.config['traffic_source_ids']['push_house']:
                    if start_date and end_date:
                        url = self.get_push_house_campaign_url(campaign.name, start_date, end_date)
                    else:
                        url = self.get_push_house_campaign_url(campaign.name)
                else:
                    if start_date and end_date:
                        url = self.get_ungads_campaign_url(campaign.name, start_date, end_date)
                    else:
                        url = self.get_ungads_campaign_url(campaign.name)

                response = requests.get(url)

                # If the response was successful, no Exception will be raised
                response.raise_for_status()
            except HTTPError as http_err:
                logging.error(f'HTTP error occurred: {http_err}')  # Python 3.6
            except Exception as err:
                logging.error(f'Other error occurred: {err}')  # Python 3.6
            else:
                campaign = self.parse_ts_campaign_json(campaign, response.json())
                logging.debug(f'Fetched data for campaign {campaign.name} from ts {ts_id}')

        return campaigns

    def get_campaigns_statuses(self, campaigns, ts_id):
        response = None
        for campaign in campaigns:
            try:
                if int(ts_id) == self.config['traffic_source_ids']['ungads']:
                    url = self.get_campaign_status_url()
                    campaign_name = '[' + campaign.name + ']'
                    response = requests.post(url, data=campaign_name)
                    response.raise_for_status()
                else:
                    paused = PausedCampaign.query.filter_by(campaign_name=campaign.name,
                                                            traffic_source=ts_id).first()
                    if paused:
                        campaign.status = 'paused'
                    else:
                        campaign.status = 'running'

            except HTTPError as http_err:
                logging.error(f'HTTP error occurred: {http_err}')  # Python 3.6
            except Exception as err:
                logging.error(f'Other error occurred: {err}')  # Python 3.6
            else:
                if response:
                    status = self.parse_campaign_status_json(ts_id, response.json())
                    campaign.status = status

        return campaigns

    def get_campaigns(self, ts_id, start_date=None, end_date=None):
        if start_date and end_date:
            try:
                campaigns = self.get_campaigns_data_from_binom(ts_id, start_date, end_date)
                campaigns = self.get_campaigns_data_from_ts(campaigns, ts_id, start_date, end_date)
                campaigns = self.get_campaigns_statuses(campaigns, ts_id)
            except Exception as e:
                logging.error(f'{e}. Trying again')
                campaigns = self.get_campaigns_data_from_binom(ts_id, start_date, end_date)
                campaigns = self.get_campaigns_data_from_ts(campaigns, ts_id, start_date, end_date)
                campaigns = self.get_campaigns_statuses(campaigns, ts_id)
        else:
            campaigns = self.get_campaigns_data_from_binom(ts_id)
            campaigns = self.get_campaigns_data_from_ts(campaigns, ts_id)
            campaigns = self.get_campaigns_statuses(campaigns, ts_id)

        return campaigns

    def get_sources_data_from_binom(self, ts_id, start_date=None, end_date=None):
        try:
            if start_date and end_date:
                url = self.get_binom_sources_url(ts_id, start_date, end_date)
            else:
                url = self.get_binom_sources_url(ts_id)

            response_json = None
            while not response_json or 'Exception' in str(response_json):
                response = requests.get(url)
                if response.text == 'null':
                    break
                response_json = response.json()
                logging.debug(f"{str(response_json)[0:300]}... (output suppressed)")
                time.sleep(3)

            # If the response was successful, no Exception will be raised
            response.raise_for_status()
        except HTTPError as http_err:
            logging.error(f'HTTP error occurred: {http_err}')  # Python 3.6
        except Exception as err:
            logging.error(f'Other error occurred: {err}')  # Python 3.6
        else:
            logging.debug(f'Fetched sources data from binom (ts={ts_id})')

            return self.parse_binom_sources_json(response.json(), ts_id)

    def get_sources_data_from_ts(self, campaigns, sources, ts_id, start_date=None, end_date=None):
        result_sources = []
        for campaign in campaigns:
            try:
                if int(ts_id) == self.config['traffic_source_ids']['push_house']:
                    if start_date and end_date:
                        url = self.get_push_house_sources_url(campaign.name, start_date, end_date)
                    else:
                        url = self.get_push_house_sources_url(campaign.name)
                else:
                    if start_date and end_date:
                        url = self.get_ungads_publishers_url(campaign.name, start_date, end_date)
                    else:
                        url = self.get_ungads_publishers_url(campaign.name)

                response = requests.get(url)

                # If the response was successful, no Exception will be raised
                response.raise_for_status()
            except HTTPError as http_err:
                logging.error(f'HTTP error occurred: {http_err}')  # Python 3.6
            except Exception as err:
                logging.error(f'Other error occurred: {err}')  # Python 3.6
            else:
                campaign_sources = self.parse_ts_sources_json(campaign.name, sources, ts_id, response.json())
                logging.debug(f'Fetched data for sources with campaign_name {campaign.name} from ts {ts_id}')
                result_sources += campaign_sources

        return result_sources

    def get_sources_statuses(self, sources, ts_id):
        for source in sources:
            paused = PausedSource.query.filter_by(source_name=source.name,
                                                  campaign_name=source.campaign_name,
                                                  traffic_source=ts_id).first()
            if paused:
                source.status = 'paused'
            else:
                source.status = 'running*'
        return sources

    def get_sources(self, campaigns, ts_id, start_date=None, end_date=None):
        try:
            sources = self.get_sources_data_from_binom(ts_id, start_date, end_date)
            sources = self.get_sources_data_from_ts(campaigns, sources, ts_id, start_date, end_date)
            sources = self.get_sources_statuses(sources, ts_id)
        except Exception as e:
            logging.error(f'{e}. Trying again')
            sources = self.get_sources_data_from_binom(ts_id, start_date, end_date)
            sources = self.get_sources_data_from_ts(campaigns, sources, ts_id, start_date, end_date)
            sources = self.get_sources_statuses(sources, ts_id)

        return sources

    def get_campaign_start_url(self, campaign_name, ts_id):
        if int(ts_id) == self.config['traffic_source_ids']['push_house']:
            start_url = self.config['push_house_urls']['campaign_action']
            api_key = self.config["api_keys"]["push_house"]

            start_url = f'{start_url}{api_key}/1/{campaign_name}'
        else:
            start_url = self.config['ungads_urls']['campaign_action']
            api_key = self.config["api_keys"]["ungads"]

            start_url = start_url.replace('[API_KEY]', api_key)
            start_url = start_url.replace('[CAMPAIGN_ID]', campaign_name)
            start_url += '/play'

        return start_url

    def get_campaign_stop_url(self, campaign_name, ts_id):
        if int(ts_id) == self.config['traffic_source_ids']['push_house']:
            stop_url = self.config['push_house_urls']['campaign_action']

            api_key = self.config["api_keys"]["push_house"]
            stop_url = f'{stop_url}{api_key}/0/{campaign_name}'
        else:
            stop_url = self.config['ungads_urls']['campaign_action']
            api_key = self.config["api_keys"]["ungads"]

            stop_url = stop_url.replace('[API_KEY]', api_key)
            stop_url = stop_url.replace('[CAMPAIGN_ID]', campaign_name)
            stop_url += '/pause'

        return stop_url

    def get_source_clear_list_url(self, campaign_name):
        clear_url = self.config['push_house_urls']['source_action']

        api_key = self.config["api_keys"]["push_house"]
        clear_url = f'{clear_url}{api_key}/clear/{campaign_name}'

        return clear_url

    def clear_source_lists(self, campaign_name):
        try:
            url = self.get_source_clear_list_url(campaign_name)

            response = requests.post(url)

            # If the response was successful, no Exception will be raised
            response.raise_for_status()
        except HTTPError as http_err:
            logging.error(f'HTTP error occurred: {http_err}')  # Python 3.6
        except Exception as err:
            logging.error(f'Other error occurred: {err}')  # Python 3.6
        else:
            logging.info(f'Cleared blacklist for campaign ' + campaign_name)
            logging.debug(response.json())

    def start_campaign(self, campaign_name, ts_id):
        try:
            url = self.get_campaign_start_url(campaign_name, ts_id)
            paused = PausedCampaign.query.filter_by(campaign_name=campaign_name,
                                                    traffic_source=ts_id).first()
            if not paused:
                return

            response = requests.get(url)
            response.raise_for_status()
            logging.info(f"Applying rule for campaign {campaign_name}")

            PausedCampaign.query.filter_by(campaign_name=campaign_name,
                                           traffic_source=ts_id).delete()
            db.session.commit()
        except HTTPError as http_err:
            logging.error(f'HTTP error occurred: {http_err}')  # Python 3.6
        except Exception as err:
            logging.error(f'Other error occurred: {err}')  # Python 3.6
        else:
            logging.info('Resumed campaign ' + campaign_name)
            logging.debug(response.content)

    def stop_campaign(self, campaign_name, ts_id):
        try:
            url = self.get_campaign_stop_url(campaign_name, ts_id)
            paused = PausedCampaign.query.filter_by(campaign_name=campaign_name,
                                                    traffic_source=ts_id).first()
            if paused:
                return

            response = requests.get(url)
            response.raise_for_status()

            db.session.add(PausedCampaign(campaign_name, ts_id))
            db.session.commit()
        except HTTPError as http_err:
            logging.error(f'HTTP error occurred: {http_err}')  # Python 3.6
        except Exception as err:
            logging.error(f'Other error occurred: {err}')  # Python 3.6
        else:
            logging.info('Paused campaign ' + campaign_name)
            logging.debug(response.content)

    def get_source_blacklist_url(self, campaign_name, ts_id):
        if int(ts_id) == self.config['traffic_source_ids']['push_house']:
            black_url = self.config['push_house_urls']['source_action']

            api_key = self.config["api_keys"]["push_house"]
            black_url = f'{black_url}{api_key}/black/{campaign_name}'
        else:
            black_url = self.config['ungads_urls']['source_black']

            api_key = self.config["api_keys"]["ungads"]
            black_url = black_url.replace('[API_KEY]', api_key)
            black_url = black_url.replace('[CAMPAIGN_ID]', campaign_name)

        return black_url

    def add_sources_to_blacklist(self, campaign_name, sources_names, ts_id):
        response = None
        is_same_sources = None
        try:
            url = self.get_source_blacklist_url(campaign_name, ts_id)

            sources_names = [int(item) for item in sources_names]

            if int(ts_id) == self.config['traffic_source_ids']['push_house']:
                already_blacklisted = PausedSource.query.filter_by(campaign_name=campaign_name,
                                                                   traffic_source=ts_id).all()

                blacklisted = []
                for source_name in sources_names:
                    paused = PausedSource.query.filter_by(source_name=source_name,
                                                          campaign_name=campaign_name,
                                                          traffic_source=ts_id).first()
                    if not paused:
                        blacklisted.append(PausedSource(source_name, campaign_name, ts_id))
                        db.session.add(PausedSource(source_name, campaign_name, ts_id))
                        db.session.commit()

                if len(blacklisted) == 0:
                    return

                blacklisted = list((source.source_name for source in blacklisted))
                already_blacklisted = list((source.source_name for source in already_blacklisted))

                data = {'list': str(blacklisted + already_blacklisted).replace('[', '').replace(']', '')}
                response = requests.post(url, data=data)
                response.raise_for_status()
            else:
                blacklisted = requests.get(url)
                if blacklisted.text:
                    sources = '[' + blacklisted.text + ']'
                    sources = json.loads(sources)

                    is_same_sources = all(elem in sources_names for elem in sources)

                    if not is_same_sources:
                        sources = list(set(sources + sources_names))
                        response = requests.post(url, data=str(sources))
                        response.raise_for_status()
                else:
                    response = requests.post(url, data=str(sources_names))
                    response.raise_for_status()

            # If the response was successful, no Exception will be raised
        except HTTPError as http_err:
            logging.error(f'HTTP error occurred: {http_err}')  # Python 3.6
        except Exception as err:
            logging.error(f'Other error occurred: {err}')  # Python 3.6
        else:
            if response and not is_same_sources:
                logging.info(f'Source {sources_names} from campaign {campaign_name} added to blacklist')
                logging.debug(response.text)

    def remove_sources_from_blacklist(self, campaign_name, sources_names, ts_id):
        response = None
        try:
            url = self.get_source_blacklist_url(campaign_name, ts_id)

            if int(ts_id) == self.config['traffic_source_ids']['push_house']:
                already_blacklisted = PausedSource.query.filter_by(campaign_name=campaign_name,
                                                                   traffic_source=ts_id).all()
                already_blacklisted = list((source.source_name for source in already_blacklisted))

                for source_name in sources_names:
                    if source_name in already_blacklisted:
                        already_blacklisted.remove(source_name)
                        PausedSource.query.filter_by(source_name=source_name,
                                                     campaign_name=campaign_name,
                                                     traffic_source=ts_id).delete()
                        db.session.commit()

                if len(already_blacklisted) == 0:
                    self.clear_source_lists(campaign_name)
                    return

                data = {'list': str(already_blacklisted).replace('[', '').replace(']', '')}
                response = requests.post(url, data=data)
                response.raise_for_status()
            else:
                sources_names = [int(item) for item in sources_names]

                blacklisted = requests.get(url)
                if blacklisted.text:
                    sources = '[' + blacklisted.text + ']'
                    sources = json.loads(sources)

                    sources = set(sources)
                    sources_names = set(sources_names)
                    sources = list(sources - sources_names)
                    response = requests.post(url, data=str(sources))
                    response.raise_for_status()

        except HTTPError as http_err:
            logging.error(f'HTTP error occurred: {http_err}')  # Python 3.6
        except Exception as err:
            logging.error(f'Other error occurred: {err}')  # Python 3.6
        else:
            if response:
                logging.info(f'Source {sources_names} removed from blacklist')
                logging.debug(response.text)

    def check_campaign_rules(self):
        rules = CampaignRule.query.all()
        now = datetime.now()

        for rule in rules:
            if rule.campaign_name != '*':
                campaigns = DailyCampaign.query.filter(
                    and_(
                        DailyCampaign.name == rule.campaign_name,
                        DailyCampaign.fetched_at >= now - timedelta(days=rule.days))
                ).all()

                current_campaigns = Campaign.query.filter(
                    and_(
                        Campaign.name == rule.campaign_name,
                        Campaign.fetched_at >= now - timedelta(days=rule.days))
                ).all()
            else:
                campaigns = DailyCampaign.query.filter(
                    DailyCampaign.fetched_at >= now - timedelta(days=rule.days)).all()

                current_campaigns = Campaign.query.filter(
                    Campaign.fetched_at >= now - timedelta(days=rule.days)).all()

            campaigns = campaigns + current_campaigns

            unique_campaigns_names = set()
            [unique_campaigns_names.add(camp.name) for camp in campaigns if camp.name not in unique_campaigns_names]

            campaigns_stats_list = []
            for name in unique_campaigns_names:
                campaign_stat = Campaign(name, 0, 0)
                campaign_stat.cost = 0
                campaign_stat.profit = 0

                for campaign in campaigns:
                    if campaign.name == name:
                        campaign_stat.traffic_source = campaign.traffic_source
                        campaign_stat.revenue += campaign.revenue
                        campaign_stat.cost += campaign.cost
                        campaign_stat.profit += campaign.profit

                campaigns_stats_list.append(campaign_stat)

            for campaign in campaigns_stats_list:
                boolean_list = []
                for num in range(int(rule.conditions)):
                    num = num + 1
                    campaign_value = getattr(campaign, getattr(rule, f'param{num}'))
                    operator = get_comparison_operator(getattr(rule, f'sign{num}'))
                    rule_value = getattr(rule, f'value{num}')
                    boolean_list.append(operator(campaign_value, rule_value))

                if all(boolean_list):
                    action = get_campaign_action(getattr(rule, 'action'), self)
                    action(campaign.name, campaign.traffic_source)

    def check_source_rules(self):
        rules = SourceRule.query.all()
        now = datetime.now()

        for rule in rules:
            if rule.source_name != '*':
                current_sources = Source.query.filter(
                    and_(
                        Source.name == rule.source_name,
                        Source.campaign_name == rule.campaign_name)).all()
            else:
                current_sources = Source.query.filter(Source.campaign_name == rule.campaign_name).all()

            unique_names = set()
            [unique_names.add((source.name, source.campaign_name)) for source in current_sources if
             (source.name, source.campaign_name) not in unique_names]

            sources_stats_list = []
            for names in unique_names:
                source_stat = Source(names[0], names[1], 0, 0)

                source_list = DailySource.query.filter(
                    and_(DailySource.name == names[0],
                         DailySource.campaign_name == names[1],
                         DailySource.fetched_at >= now - timedelta(days=rule.days))).all()
                current_source_list = Source.query.filter(
                    and_(Source.name == names[0],
                         Source.campaign_name == names[1])).all()

                source_list = source_list + current_source_list

                for source in source_list:
                    source_stat.traffic_source = source.traffic_source
                    source_stat.revenue += source.revenue
                    source_stat.binom_clicks += source.binom_clicks
                    source_stat.lp_clicks += source.lp_clicks
                    source_stat.leads += source.leads

                    source_stat.cost += source.cost
                    source_stat.clicks += source.clicks
                    source_stat.impressions += source.impressions

                    if source_stat.leads != 0:
                        source_stat.payout = source_stat.revenue / source_stat.leads

                    source_stat.profit = source_stat.revenue - source_stat.cost

                    if source_stat.clicks != 0:
                        source_stat.cpc = source_stat.cost / source_stat.clicks
                        source_stat.epc = source_stat.revenue / source_stat.clicks

                    if source_stat.binom_clicks != 0:
                        source_stat.lp_ctr = source_stat.lp_clicks / source_stat.binom_clicks * 100

                    if source_stat.cost != 0:
                        source_stat.roi = source_stat.profit / source_stat.cost * 100

                    if source_stat.impressions != 0:
                        source_stat.ctr = source_stat.clicks / source_stat.impressions * 100
                        source_stat.cpm = source_stat.cost / source_stat.impressions * 1000

                sources_stats_list.append(source_stat)

            appropriate_sources = []
            if len(sources_stats_list) != 0:
                campaign_name = sources_stats_list[0].campaign_name
                traffic_source = sources_stats_list[0].traffic_source

            for source in sources_stats_list:
                boolean_list = []
                for num in range(int(rule.conditions)):
                    num = num + 1
                    source_value = getattr(source, getattr(rule, f'param{num}'))
                    operator = get_comparison_operator(getattr(rule, f'sign{num}'))
                    rule_value = getattr(rule, f'value{num}')
                    boolean_list.append(operator(source_value, rule_value))

                if all(boolean_list):
                    appropriate_sources.append(source.name)

            if len(appropriate_sources) != 0:
                # logging.info(f"Applying rule for source id {rule.source_name} for campaign {rule.campaign_name}")

                action = get_source_action(getattr(rule, 'action'), self)
                action(campaign_name, appropriate_sources, traffic_source)
