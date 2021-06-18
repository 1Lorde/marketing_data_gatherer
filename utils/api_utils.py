import json
import logging
import time
from datetime import datetime, timedelta

import requests
from requests import HTTPError
from sqlalchemy.sql.expression import and_

from gatherer.utils import is_push_house, is_ungads
from models.models import Campaign, Source, DailyCampaign, CampaignRule, DailySource, SourceRule, db, PausedSource, \
    PausedCampaign, Binom, TrafficSource
from utils.rules_utils import get_comparison_operator, get_campaign_action, get_source_action


class ApiUtils:
    def __init__(self, config):
        self.config = config

    def get_binom_campaigns_url(self, ts: TrafficSource, binom: Binom, start_date=None, end_date=None):
        if is_push_house(ts):
            campaigns_url = self.config['binom_urls']['ph_campaigns']
        elif is_ungads(ts):
            campaigns_url = self.config['binom_urls']['ungads_campaigns']
        else:
            return None

        if start_date and end_date:
            start_date = start_date.strftime("%Y-%m-%d")
            end_date = end_date.strftime("%Y-%m-%d")

            campaigns_url = campaigns_url.replace('[DATE_S]', start_date)
            campaigns_url = campaigns_url.replace('[DATE_E]', end_date)
        else:
            current_date = datetime.now().strftime("%Y-%m-%d")
            campaigns_url = campaigns_url.replace('[DATE_S]', current_date)
            campaigns_url = campaigns_url.replace('[DATE_E]', current_date)

        campaigns_url = campaigns_url.replace('[TS_ID]', ts.binom_ts_id)
        campaigns_url = campaigns_url.replace('[BINOM_URL]', binom.url)
        campaigns_url = f'{campaigns_url}&api_key={binom.api_key}'

        return campaigns_url

    def get_push_house_campaign_url(self, campaign_name, ts: TrafficSource, start_date=None, end_date=None):
        stats_url = self.config['push_house_urls']['stats']

        if start_date and end_date:
            start_date = start_date.strftime("%Y-%m-%d")
            end_date = end_date.strftime("%Y-%m-%d")

            stats_url = f'{stats_url}{ts.credentials.api_key}/date/{start_date}/{end_date}/{campaign_name}'
        else:
            current_date = datetime.now().strftime("%Y-%m-%d")
            stats_url = f'{stats_url}{ts.credentials.api_key}/date/{current_date}/{current_date}/{campaign_name}'

        return stats_url

    def get_ungads_campaign_url(self, campaign_name, ts: TrafficSource, start_date=None, end_date=None):
        stats_url = self.config['ungads_urls']['stats']
        stats_url = stats_url.replace('[API_KEY]', ts.credentials.api_key)

        if start_date and end_date:
            start_date = start_date.strftime("%Y-%m-%d")
            end_date = end_date.strftime("%Y-%m-%d")

            stats_url = f'{stats_url}?date_start={start_date}&date_finish={end_date}&campaign_id={campaign_name}'
        else:
            stats_url = f'{stats_url}?campaign_id={campaign_name}'

        return stats_url

    def get_binom_sources_url(self, ts: TrafficSource, binom: Binom, start_date=None, end_date=None):
        if is_push_house(ts):
            sources_url = self.config['binom_urls']['ph_sources']
        elif is_ungads(ts):
            sources_url = self.config['binom_urls']['ungads_sources']
        else:
            return None

        if start_date and end_date:
            start_date = start_date.strftime("%Y-%m-%d")
            end_date = end_date.strftime("%Y-%m-%d")

            sources_url = sources_url.replace('[DATE_S]', start_date)
            sources_url = sources_url.replace('[DATE_E]', end_date)
        else:
            current_date = datetime.now().strftime("%Y-%m-%d")
            sources_url = sources_url.replace('[DATE_S]', current_date)
            sources_url = sources_url.replace('[DATE_E]', current_date)

        sources_url = sources_url.replace('[TS_ID]', ts.binom_ts_id)
        sources_url = sources_url.replace('[BINOM_URL]', binom.url)
        sources_url = f'{sources_url}&api_key={binom.api_key}'

        return sources_url

    def get_push_house_sources_url(self, campaign_name, ts: TrafficSource, start_date=None, end_date=None):
        stats_url = self.config['push_house_urls']['stats']

        if start_date and end_date:
            start_date = start_date.strftime("%Y-%m-%d")
            end_date = end_date.strftime("%Y-%m-%d")

            stats_url = f'{stats_url}{ts.credentials.api_key}/subacc/{start_date}/{end_date}/{campaign_name}'
        else:
            current_date = datetime.now().strftime("%Y-%m-%d")
            stats_url = f'{stats_url}{ts.credentials.api_key}/subacc/{current_date}/{current_date}/{campaign_name}'

        return stats_url

    def get_ungads_publishers_url(self, campaign_name, ts, start_date=None, end_date=None):
        stats_url = self.config['ungads_urls']['stats']
        stats_url = stats_url.replace('[API_KEY]', ts.credentials.api_key)

        if start_date and end_date:
            start_date = start_date.strftime("%Y-%m-%d")
            end_date = end_date.strftime("%Y-%m-%d")

            stats_url = f'{stats_url}?group_by[]=publisher&group_by[]=date&date_start={start_date}&date_finish={end_date}&campaign_id={campaign_name}'
        else:
            stats_url = f'{stats_url}?group_by[]=publisher&group_by[]=date&campaign_id={campaign_name}'

        return stats_url

    def get_campaign_status_url(self, ts: TrafficSource):
        status_url = self.config['ungads_urls']['campaign_status']
        status_url = status_url.replace('[API_KEY]', ts.credentials.api_key)
        return status_url

    def get_binom_traffic_sources_url(self, binom: Binom):
        ts_url = self.config['binom_urls']['traffic_sources']

        ts_url = ts_url.replace('[BINOM_URL]', binom.url)
        ts_url = f'{ts_url}&api_key={binom.api_key}'
        return ts_url

    def parse_binom_campaigns_json(self, json, ts: TrafficSource, binom: Binom):
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
                    campaign = Campaign(name, revenue, ts.binom_ts_id)
                    campaign.binom_source = binom.name
                    campaign.binom_clicks = int(element['clicks'])
                    campaign.lp_clicks = int(element['lp_clicks'])
                    campaign.leads = int(element['leads'])
                    if campaign.leads != 0:
                        campaign.payout = campaign.revenue / campaign.leads
                    campaigns.append(campaign)
                except:
                    logging.error('Parsing campaigns json error')

        return campaigns

    def parse_ts_campaign_json(self, campaign, json, ts: TrafficSource):
        if not json:
            return campaign

        if is_push_house(ts):
            campaign.clicks = float(json[0]['clicks'])
            campaign.impressions = float(json[0]['shows'])
            campaign.cost = float(json[0]['cost'])
        elif is_ungads(ts):
            campaign.clicks = float(json[0]['clicks'])
            campaign.impressions = float(json[0]['impressions'])
            campaign.cost = float(json[0]['spent_advertiser'])
        else:
            return None

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

    def parse_campaign_status_json(self, ts: TrafficSource, json):
        if not json or is_push_house(ts):
            return 'undefined'
        elif is_ungads(ts):
            return json[next(iter(json))]['status']
        else:
            return None

    def parse_binom_sources_json(self, json, ts, binom):
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
                    source = Source(name, campaign_name, revenue, ts.binom_ts_id)
                    source.binom_source = binom.name
                    source.binom_clicks = int(element['clicks'])
                    source.lp_clicks = int(element['lp_clicks'])
                    source.leads = int(element['leads'])
                    if source.leads != 0:
                        source.payout = source.revenue / source.leads
                    sources.append(source)
                except Exception as e:
                    logging.error('Parsing sources json error ' + str(e))

        return sources

    def parse_ts_sources_json(self, campaign_name, sources, json):
        if not json:
            return sources

        if not sources:
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

    def parse_binom_traffic_sources_json(self, json, binom):
        traffic_sources = []
        if not json:
            return traffic_sources

        for element in json:
            try:
                if 'name' not in element:
                    continue

                name = element['name']
                ts_id = element['id']
                url = element['postback_url']
                traffic_source = TrafficSource(name, ts_id, binom.id, -1)

                if 'push' and 'house' in url:
                    traffic_source.url = 'https://push.house/'
                elif 'ungads' in url:
                    traffic_source.url = 'https://ungads.com/'

                traffic_sources.append(traffic_source)
            except:
                logging.error('Parsing traffic sources json error')

        return traffic_sources

    def get_binom_traffic_sources(self, binom):
        try:
            url = self.get_binom_traffic_sources_url(binom)
            response_json = None
            while not response_json or 'Exception' in str(response_json):
                response = requests.get(url)
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
            logging.debug(f'Fetched traffic sources for binom {binom.name}')
            return self.parse_binom_traffic_sources_json(response.json(), binom)

    def get_campaigns_data_from_binom(self, ts: TrafficSource, binom: Binom, start_date=None, end_date=None):
        try:
            if start_date and end_date:
                url = self.get_binom_campaigns_url(ts, binom, start_date, end_date)
            else:
                url = self.get_binom_campaigns_url(ts, binom)

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
            logging.debug(f'Fetched campaigns data from binom (ts={ts.binom_ts_id})')
            return self.parse_binom_campaigns_json(response.json(), ts, binom)

    def get_campaigns_data_from_ts(self, campaigns, ts: TrafficSource, start_date=None, end_date=None):
        for campaign in campaigns:
            try:
                if is_push_house(ts):
                    if start_date and end_date:
                        url = self.get_push_house_campaign_url(campaign.name, ts, start_date, end_date)
                    else:
                        url = self.get_push_house_campaign_url(campaign.name, ts)
                elif is_ungads(ts):
                    if start_date and end_date:
                        url = self.get_ungads_campaign_url(campaign.name, ts, start_date, end_date)
                    else:
                        url = self.get_ungads_campaign_url(campaign.name, ts)

                response = requests.get(url)

                # If the response was successful, no Exception will be raised
                response.raise_for_status()
            except HTTPError as http_err:
                logging.error(f'HTTP error occurred: {http_err}')  # Python 3.6
            except Exception as err:
                logging.error(f'Other error occurred: {err}')  # Python 3.6
            else:
                if response:
                    campaign = self.parse_ts_campaign_json(campaign, response.json(), ts)
                    logging.debug(f'Fetched data for campaign {campaign.name} from ts {ts.binom_ts_id}')

        return campaigns

    def get_campaigns_statuses(self, campaigns, ts: TrafficSource):
        response = None
        for campaign in campaigns:
            try:
                if is_ungads(ts):
                    url = self.get_campaign_status_url(ts)
                    campaign_name = '[' + campaign.name + ']'
                    response = requests.post(url, data=campaign_name)
                    response.raise_for_status()
                elif is_push_house(ts):
                    paused = PausedCampaign.query.filter_by(campaign_name=campaign.name,
                                                            ts_id=ts.id).first()
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
                    status = self.parse_campaign_status_json(ts, response.json())
                    campaign.status = status

        return campaigns

    def get_campaigns(self, ts: TrafficSource, binom: Binom, start_date=None, end_date=None):
        campaigns = self.get_campaigns_data_from_binom(ts, binom, start_date, end_date)
        campaigns = self.get_campaigns_data_from_ts(campaigns, ts, start_date, end_date)
        campaigns = self.get_campaigns_statuses(campaigns, ts)
        return campaigns

    def get_sources_data_from_binom(self, ts: TrafficSource, binom: Binom, start_date=None, end_date=None):
        try:
            if start_date and end_date:
                url = self.get_binom_sources_url(ts, binom, start_date, end_date)
            else:
                url = self.get_binom_sources_url(ts, binom)

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
            logging.debug(f'Fetched sources data from binom (ts={ts.binom_ts_id})')

            return self.parse_binom_sources_json(response.json(), ts, binom)

    def get_sources_data_from_ts(self, campaigns, sources, ts: TrafficSource, start_date=None, end_date=None):
        result_sources = []
        for campaign in campaigns:
            try:
                if is_push_house(ts):
                    if start_date and end_date:
                        url = self.get_push_house_sources_url(campaign.name, ts, start_date, end_date)
                    else:
                        url = self.get_push_house_sources_url(campaign.name, ts)
                else:
                    if start_date and end_date:
                        url = self.get_ungads_publishers_url(campaign.name, ts, start_date, end_date)
                    else:
                        url = self.get_ungads_publishers_url(campaign.name, ts)

                response = requests.get(url)

                # If the response was successful, no Exception will be raised
                response.raise_for_status()
            except HTTPError as http_err:
                logging.error(f'HTTP error occurred: {http_err}')  # Python 3.6
            except Exception as err:
                logging.error(f'Other error occurred: {err}')  # Python 3.6
            else:
                campaign_sources = self.parse_ts_sources_json(campaign.name, sources, response.json())
                logging.debug(f'Fetched data for sources with campaign_name {campaign.name} from ts {ts.binom_ts_id}')
                if campaign_sources:
                    result_sources += campaign_sources

        return result_sources

    def get_sources_statuses(self, sources, ts: TrafficSource):
        for source in sources:
            paused = PausedSource.query.filter_by(source_name=source.name,
                                                  campaign_name=source.campaign_name,
                                                  ts_id=ts.id).first()
            if paused:
                source.status = 'paused'
            else:
                source.status = 'running'
        return sources

    def get_sources(self, campaigns, ts: TrafficSource, binom: Binom, start_date=None, end_date=None):
        sources = self.get_sources_data_from_binom(ts, binom, start_date, end_date)
        sources = self.get_sources_data_from_ts(campaigns, sources, ts, start_date, end_date)
        sources = self.get_sources_statuses(sources, ts)
        return sources

    def get_campaign_start_url(self, campaign_name, ts: TrafficSource):
        if is_push_house(ts):
            start_url = self.config['push_house_urls']['campaign_action']
            start_url = f'{start_url}{ts.credentials.api_key}/1/{campaign_name}'
        elif is_ungads(ts):
            start_url = self.config['ungads_urls']['campaign_action']
            start_url = start_url.replace('[API_KEY]', ts.credentials.api_key)
            start_url = start_url.replace('[CAMPAIGN_ID]', campaign_name)
            start_url += '/play'
        else:
            return None

        return start_url

    def get_campaign_stop_url(self, campaign_name, ts):
        if is_push_house(ts):
            stop_url = self.config['push_house_urls']['campaign_action']
            stop_url = f'{stop_url}{ts.credentials.api_key}/0/{campaign_name}'
        elif is_ungads(ts):
            stop_url = self.config['ungads_urls']['campaign_action']
            stop_url = stop_url.replace('[API_KEY]', ts.credentials.api_key)
            stop_url = stop_url.replace('[CAMPAIGN_ID]', campaign_name)
            stop_url += '/pause'
        else:
            return None

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

    def start_campaign(self, campaign_name, ts: TrafficSource):
        try:
            url = self.get_campaign_start_url(campaign_name, ts)
            paused = PausedCampaign.query.filter_by(campaign_name=campaign_name,
                                                    ts_id=ts.id).first()
            if not paused:
                return

            response = requests.get(url)
            response.raise_for_status()
            logging.info(f"Applying rule for campaign {campaign_name}")

            PausedCampaign.query.filter_by(campaign_name=campaign_name,
                                           ts_id=ts.id).delete()
            db.session.commit()
        except HTTPError as http_err:
            logging.error(f'HTTP error occurred: {http_err}')  # Python 3.6
        except Exception as err:
            logging.error(f'Other error occurred: {err}')  # Python 3.6
        else:
            logging.info('Resumed campaign ' + campaign_name)
            logging.debug(response.content)

    def stop_campaign(self, campaign_name, ts: TrafficSource):
        try:
            url = self.get_campaign_stop_url(campaign_name, ts)
            paused = PausedCampaign.query.filter_by(campaign_name=campaign_name,
                                                    ts_id=ts.id).first()
            if paused:
                return

            response = requests.get(url)
            response.raise_for_status()

            db.session.add(PausedCampaign(campaign_name, ts))
            db.session.commit()
        except HTTPError as http_err:
            logging.error(f'HTTP error occurred: {http_err}')  # Python 3.6
        except Exception as err:
            logging.error(f'Other error occurred: {err}')  # Python 3.6
        else:
            logging.info('Paused campaign ' + campaign_name)
            logging.debug(response.content)

    def get_source_blacklist_url(self, campaign_name, ts: TrafficSource):
        if is_push_house(ts):
            black_url = self.config['push_house_urls']['source_action']
            black_url = f'{black_url}{ts.credentials.api_key}/black/{campaign_name}'
        elif is_ungads(ts):
            black_url = self.config['ungads_urls']['source_black']
            black_url = black_url.replace('[API_KEY]', ts.credentials.api_key)
            black_url = black_url.replace('[CAMPAIGN_ID]', campaign_name)
        else:
            return None

        return black_url

    def add_sources_to_blacklist(self, campaign_name, sources_names, ts: TrafficSource):
        response = None
        is_same_sources = None
        try:
            url = self.get_source_blacklist_url(campaign_name, ts)

            sources_names = [int(item) for item in sources_names]

            if is_push_house(ts):
                already_blacklisted = PausedSource.query.filter_by(campaign_name=campaign_name,
                                                                   ts_id=ts.id).all()

                blacklisted = []
                for source_name in sources_names:
                    paused = PausedSource.query.filter_by(source_name=source_name,
                                                          campaign_name=campaign_name,
                                                          ts_id=ts.id).first()
                    if not paused:
                        blacklisted.append(PausedSource(source_name, campaign_name, ts))
                        db.session.add(PausedSource(source_name, campaign_name, ts))
                        db.session.commit()

                if len(blacklisted) == 0:
                    return

                blacklisted = list((source.source_name for source in blacklisted))
                already_blacklisted = list((source.source_name for source in already_blacklisted))

                data = {'list': str(blacklisted + already_blacklisted).replace('[', '').replace(']', '')}
                response = requests.post(url, data=data)
                response.raise_for_status()
            elif is_ungads(ts):
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

    def remove_sources_from_blacklist(self, campaign_name, sources_names, ts: TrafficSource):
        response = None
        try:
            url = self.get_source_blacklist_url(campaign_name, ts)

            if is_push_house(ts):
                already_blacklisted = PausedSource.query.filter_by(campaign_name=campaign_name,
                                                                   ts_id=ts.id).all()
                already_blacklisted = list((source.source_name for source in already_blacklisted))

                for source_name in sources_names:
                    if source_name in already_blacklisted:
                        already_blacklisted.remove(source_name)
                        PausedSource.query.filter_by(source_name=source_name,
                                                     campaign_name=campaign_name,
                                                     ts_id=ts.id).delete()
                        db.session.commit()

                if len(already_blacklisted) == 0:
                    self.clear_source_lists(campaign_name)
                    return

                data = {'list': str(already_blacklisted).replace('[', '').replace(']', '')}
                response = requests.post(url, data=data)
                response.raise_for_status()
            elif is_ungads(ts):
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
                        DailyCampaign.fetched_at >= now - timedelta(days=rule.days),
                        DailyCampaign.traffic_source == rule.ts.binom_ts_id,
                        DailyCampaign.binom_source == rule.ts.binom.name)
                ).all()

                current_campaigns = Campaign.query.filter(
                    and_(
                        Campaign.name == rule.campaign_name,
                        Campaign.fetched_at >= now - timedelta(days=rule.days),
                        Campaign.traffic_source == rule.ts.binom_ts_id,
                        Campaign.binom_source == rule.ts.binom.name
                    )
                ).all()
            else:
                campaigns = DailyCampaign.query.filter(
                    and_(
                        DailyCampaign.fetched_at >= now - timedelta(days=rule.days),
                        DailyCampaign.traffic_source == rule.ts.binom_ts_id,
                        DailyCampaign.binom_source == rule.ts.binom.name
                    )
                ).all()

                current_campaigns = Campaign.query.filter(
                    and_(
                        Campaign.fetched_at >= now - timedelta(days=rule.days),
                        Campaign.traffic_source == rule.ts.binom_ts_id,
                        Campaign.binom_source == rule.ts.binom.name
                    )
                ).all()

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
                        if campaign_stat.binom_source == 'undefined':
                            campaign_stat.binom_source = campaign.binom_source

                        campaign_stat.traffic_source = campaign.traffic_source
                        campaign_stat.revenue += campaign.revenue
                        campaign_stat.binom_clicks += campaign.binom_clicks
                        campaign_stat.lp_clicks += campaign.lp_clicks
                        campaign_stat.leads += campaign.leads

                        campaign_stat.cost += campaign.cost
                        campaign_stat.clicks += campaign.clicks
                        campaign_stat.impressions += campaign.impressions

                    if campaign_stat.leads != 0:
                        campaign_stat.payout = campaign_stat.revenue / campaign_stat.leads

                    campaign_stat.profit = campaign_stat.revenue - campaign_stat.cost

                    if campaign_stat.clicks != 0:
                        campaign_stat.cpc = campaign_stat.cost / campaign_stat.clicks
                        campaign_stat.epc = campaign_stat.revenue / campaign_stat.clicks

                    if campaign_stat.binom_clicks != 0:
                        campaign_stat.lp_ctr = campaign_stat.lp_clicks / campaign_stat.binom_clicks * 100

                    if campaign_stat.cost != 0:
                        campaign_stat.roi = campaign_stat.profit / campaign_stat.cost * 100

                    if campaign_stat.impressions != 0:
                        campaign_stat.ctr = campaign_stat.clicks / campaign_stat.impressions * 100
                        campaign_stat.cpm = campaign_stat.cost / campaign_stat.impressions * 1000

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
                    binom = Binom.query.filter_by(name=campaign.binom_source).first()
                    ts = TrafficSource.query.filter(
                        and_(
                            TrafficSource.binom_ts_id == campaign.traffic_source,
                            TrafficSource.binom_id == binom.id
                        )
                    ).first()
                    action(campaign.name, ts)

    def check_source_rules(self):
        rules = SourceRule.query.all()
        now = datetime.now()

        for rule in rules:
            if rule.source_name != '*':
                if rule.campaign_name != '*':
                    sources_list = DailySource.query.filter(
                        and_(
                            DailySource.name == rule.source_name,
                            DailySource.campaign_name == rule.campaign_name,
                            DailySource.traffic_source == rule.ts.binom_ts_id,
                            DailySource.binom_source == rule.ts.binom.name
                        )
                    ).all()

                    current_sources = Source.query.filter(
                        and_(
                            Source.name == rule.source_name,
                            Source.campaign_name == rule.campaign_name,
                            Source.traffic_source == rule.ts.binom_ts_id,
                            Source.binom_source == rule.ts.binom.name
                        )
                    ).all()
                else:
                    sources_list = DailySource.query.filter(
                        and_(
                            DailySource.name == rule.source_name,
                            DailySource.traffic_source == rule.ts.binom_ts_id,
                            DailySource.binom_source == rule.ts.binom.name
                        )
                    ).all()

                    current_sources = Source.query.filter(
                        and_(
                            Source.name == rule.source_name,
                            Source.traffic_source == rule.ts.binom_ts_id,
                            Source.binom_source == rule.ts.binom.name
                        )
                    ).all()
            else:
                if rule.campaign_name != '*':
                    sources_list = DailySource.query.filter(
                        and_(
                            DailySource.campaign_name == rule.campaign_name,
                            DailySource.traffic_source == rule.ts.binom_ts_id,
                            DailySource.binom_source == rule.ts.binom.name
                        )
                    ).all()

                    current_sources = Source.query.filter(
                        and_(
                            Source.campaign_name == rule.campaign_name,
                            Source.traffic_source == rule.ts.binom_ts_id,
                            Source.binom_source == rule.ts.binom.name
                        )
                    ).all()
                else:
                    sources_list = DailySource.query.filter(
                        and_(
                            DailySource.traffic_source == rule.ts.binom_ts_id,
                            DailySource.binom_source == rule.ts.binom.name
                        )
                    ).all()

                    current_sources = Source.query.filter(
                        and_(
                            Source.traffic_source == rule.ts.binom_ts_id,
                            Source.binom_source == rule.ts.binom.name
                        )
                    ).all()

            sources_list = sources_list + current_sources

            unique_names = set()
            [unique_names.add((source.name, source.campaign_name)) for source in sources_list if
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
                    source_stat.binom_source = source.binom_source
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
                binom_source = sources_stats_list[0].binom_source

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

                binom = Binom.query.filter_by(name=binom_source).first()
                ts = TrafficSource.query.filter(
                    and_(
                        TrafficSource.binom_ts_id == traffic_source,
                        TrafficSource.binom_id == binom.id
                    )
                ).first()
                action(campaign_name, appropriate_sources, ts)
