import logging
from datetime import datetime

import requests
from requests import HTTPError

from models.models import Campaign, Source, DailyCampaign, CampaignRule, DailySource, SourceRule
from utils.rules_utils import get_comparison_operator, get_campaign_action, get_source_action


class ApiUtils:
    def __init__(self, config):
        self.config = config

    def get_binom_campaigns_url(self, ts_id, start_date=None, end_date=None):
        if ts_id == self.config['traffic_source_ids']['push_house']:
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
        if ts_id == self.config['traffic_source_ids']['push_house']:
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

            stats_url = f'{stats_url}?group_by[]=publisher&group_by[]=date&group_by[]=creative_id&date_start={start_date}&date_finish={end_date}&campaign_id={campaign_name}'
        else:
            stats_url = f'{stats_url}?group_by[]=publisher&group_by[]=date&group_by[]=creative_id&campaign_id={campaign_name}'

        return stats_url

    def parse_campaigns_json(self, json, ts_id):
        campaigns = []
        for element in json:
            name = element['name']

            if not name.isdigit():
                continue

            revenue = float(element['revenue'])
            campaign = Campaign(name, revenue, ts_id)
            campaigns.append(campaign)

        return campaigns

    def parse_campaign_cost_json(self, ts_id, json):
        if not json:
            return None

        if ts_id == self.config['traffic_source_ids']['push_house']:
            return float(json[0]['cost'])
        else:
            return float(json[0]['spent_advertiser'])

    def parse_sources_json(self, json, ts_id):
        sources = []
        campaign_name = ''

        for element in json:
            if element['level'] == '1':
                campaign_name = element['name']
                continue

            name = element['name']
            revenue = float(element['revenue'])
            source = Source(name, campaign_name, revenue, ts_id)
            sources.append(source)

        return sources

    def parse_sources_costs_json(self, campaign_name, sources, ts_id, json):
        if ts_id == self.config['traffic_source_ids']['push_house']:
            for element in json:
                for source in sources:
                    if str(element['tname']) == source.name and source.campaign_name == campaign_name:
                        source.cost = float(element['cost'])
        else:
            for element in json:
                for source in sources:
                    if str(element['publisher_id']) == source.name and source.campaign_name == campaign_name:
                        source.cost = float(element['spent_advertiser'])

        return sources

    def get_campaigns_revenues(self, ts_id, start_date=None, end_date=None):
        try:
            if start_date and end_date:
                url = self.get_binom_campaigns_url(ts_id, start_date, end_date)
            else:
                url = self.get_binom_campaigns_url(ts_id)

            response = requests.get(url)

            # If the response was successful, no Exception will be raised
            response.raise_for_status()
        except HTTPError as http_err:
            logging.error(f'HTTP error occurred: {http_err}')  # Python 3.6
        except Exception as err:
            logging.error(f'Other error occurred: {err}')  # Python 3.6
        else:
            logging.info('Fetched campaigns revenues')
            print(response.json())
            return self.parse_campaigns_json(response.json(), ts_id)

    def get_campaigns_costs(self, campaigns, ts_id, start_date=None, end_date=None):
        for campaign in campaigns:
            try:
                if ts_id == self.config['traffic_source_ids']['push_house']:
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
                cost = self.parse_campaign_cost_json(ts_id, response.json())
                logging.info(f'Fetched cost {cost} for campaign {campaign.name} from ts {ts_id}')
                campaign.cost = cost

        return campaigns

    def get_campaigns_profit(self, campaigns):
        for campaign in campaigns:
            if campaign.cost is None or campaign.revenue is None:
                campaign.profit = None
            else:
                campaign.profit = campaign.revenue - campaign.cost

        return campaigns

    def get_campaigns(self, ts_id, start_date=None, end_date=None):
        if start_date and end_date:
            try:
                campaigns = self.get_campaigns_revenues(ts_id, start_date, end_date)
                campaigns = self.get_campaigns_costs(campaigns, ts_id, start_date, end_date)
            except Exception as e:
                logging.error(f'{e}. Trying again')
                campaigns = self.get_campaigns_revenues(ts_id, start_date, end_date)
                campaigns = self.get_campaigns_costs(campaigns, ts_id, start_date, end_date)
        else:
            campaigns = self.get_campaigns_revenues(ts_id)
            campaigns = self.get_campaigns_costs(campaigns, ts_id)

        campaigns = self.get_campaigns_profit(campaigns)

        return campaigns

    def get_sources_revenues(self, ts_id, start_date=None, end_date=None):
        try:
            if start_date and end_date:
                url = self.get_binom_sources_url(ts_id, start_date, end_date)
            else:
                url = self.get_binom_sources_url(ts_id)

            response = requests.get(url)

            # If the response was successful, no Exception will be raised
            response.raise_for_status()
        except HTTPError as http_err:
            logging.error(f'HTTP error occurred: {http_err}')  # Python 3.6
        except Exception as err:
            logging.error(f'Other error occurred: {err}')  # Python 3.6
        else:
            logging.info('Fetching sources')
            print(response.json())

            return self.parse_sources_json(response.json(), ts_id)

    def get_sources_costs(self, campaigns, sources, ts_id, start_date=None, end_date=None):
        for campaign in campaigns:
            try:
                if ts_id == self.config['traffic_source_ids']['push_house']:
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
                sources = self.parse_sources_costs_json(campaign.name, sources, ts_id, response.json())
                logging.info(f'Fetched costs for sources with campaign_name {campaign.name}')

        return sources

    def get_sources_profit(self, sources):
        for source in sources:
            source.profit = source.revenue - source.cost

        return sources

    def get_sources(self, campaigns, ts_id, start_date=None, end_date=None):
        try:
            sources = self.get_sources_revenues(ts_id, start_date, end_date)
            sources = self.get_sources_costs(campaigns, sources, ts_id, start_date, end_date)
            sources = self.get_sources_profit(sources)
        except Exception as e:
            logging.error(f'{e}. Trying again')
            sources = self.get_sources_revenues(ts_id, start_date, end_date)
            sources = self.get_sources_costs(campaigns, sources, ts_id, start_date, end_date)
            sources = self.get_sources_profit(sources)

        return sources

    def get_campaign_start_url(self, campaign_name):
        start_url = self.config['push_house_urls']['campaign_action']

        api_key = self.config["api_keys"]["push_house"]
        start_url = f'{start_url}{api_key}/1/{campaign_name}'

        return start_url

    def get_campaign_stop_url(self, campaign_name):
        stop_url = self.config['push_house_urls']['campaign_action']

        api_key = self.config["api_keys"]["push_house"]
        stop_url = f'{stop_url}{api_key}/0/{campaign_name}'

        return stop_url

    def start_campaign(self, campaign_name):
        try:
            url = self.get_campaign_start_url(campaign_name)

            response = requests.get(url)

            # If the response was successful, no Exception will be raised
            response.raise_for_status()
        except HTTPError as http_err:
            logging.error(f'HTTP error occurred: {http_err}')  # Python 3.6
        except Exception as err:
            logging.error(f'Other error occurred: {err}')  # Python 3.6
        else:
            logging.info('Start campaign ' + campaign_name)
            print(response.json())

    def stop_campaign(self, campaign_name):
        try:
            url = self.get_campaign_stop_url(campaign_name)

            response = requests.get(url)

            # If the response was successful, no Exception will be raised
            response.raise_for_status()
        except HTTPError as http_err:
            logging.error(f'HTTP error occurred: {http_err}')  # Python 3.6
        except Exception as err:
            logging.error(f'Other error occurred: {err}')  # Python 3.6
        else:
            logging.info('Stop campaign ' + campaign_name)
            print(response.json())

    def get_source_whitelist_url(self, campaign_name):
        white_url = self.config['push_house_urls']['source_action']

        api_key = self.config["api_keys"]["push_house"]
        white_url = f'{white_url}{api_key}/white/{campaign_name}'

        return white_url

    def get_source_blacklist_url(self, campaign_name):
        black_url = self.config['push_house_urls']['source_action']

        api_key = self.config["api_keys"]["push_house"]
        black_url = f'{black_url}{api_key}/black/{campaign_name}'

        return black_url

    def get_source_clear_list_url(self, campaign_name):
        clear_url = self.config['push_house_urls']['source_action']

        api_key = self.config["api_keys"]["push_house"]
        clear_url = f'{clear_url}{api_key}/clear/{campaign_name}'

        return clear_url

    def add_source_to_whitelist(self, campaign_name, source_name):
        try:
            url = self.get_source_whitelist_url(campaign_name)
            data = {'list': source_name}
            response = requests.post(url, data=data)

            # If the response was successful, no Exception will be raised
            response.raise_for_status()
        except HTTPError as http_err:
            logging.error(f'HTTP error occurred: {http_err}')  # Python 3.6
        except Exception as err:
            logging.error(f'Other error occurred: {err}')  # Python 3.6
        else:
            logging.info(f'Source {source_name} added to whitelist.')
            print(response.json())

    def add_source_to_blacklist(self, campaign_name, source_name):
        try:
            url = self.get_source_blacklist_url(campaign_name)
            data = {'list': source_name}
            response = requests.post(url, data=data)

            # If the response was successful, no Exception will be raised
            response.raise_for_status()
        except HTTPError as http_err:
            logging.error(f'HTTP error occurred: {http_err}')  # Python 3.6
        except Exception as err:
            logging.error(f'Other error occurred: {err}')  # Python 3.6
        else:
            logging.info(f'Source {source_name} added to blacklist.')
            print(response.json())

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
            logging.info(f'Cleared all lists.')
            print(response.json())

    def check_campaign_rules(self):
        campaigns = DailyCampaign.query.all()
        now = datetime.now()
        for campaign in campaigns:
            delta = now - campaign.fetched_at
            rules = CampaignRule.query.filter_by(campaign_name=campaign.name, days=delta.days).all()
            for rule in rules:
                boolean_list = []
                for num in range(int(rule.conditions)):
                    num = num + 1
                    campaign_value = getattr(campaign, getattr(rule, f'param{num}'))
                    operator = get_comparison_operator(getattr(rule, f'sign{num}'))
                    rule_value = getattr(rule, f'value{num}')
                    boolean_list.append(operator(campaign_value, rule_value))

                if all(boolean_list):
                    action = get_campaign_action(getattr(rule, 'action'), self)
                    action(campaign.name)

    def check_source_rules(self):
        sources = DailySource.query.all()
        now = datetime.now()
        for source in sources:
            delta = now - source.fetched_at
            rules = SourceRule.query.filter_by(campaign_name=source.campaign_name, source_name=source.name,
                                               days=delta.days).all()
            for rule in rules:
                boolean_list = []
                for num in range(int(rule.conditions)):
                    num = num + 1
                    source_value = getattr(source, getattr(rule, f'param{num}'))
                    operator = get_comparison_operator(getattr(rule, f'sign{num}'))
                    rule_value = getattr(rule, f'value{num}')
                    boolean_list.append(operator(source_value, rule_value))

                if all(boolean_list):
                    action = get_source_action(getattr(rule, 'action'), self)
                    action(source.campaign_name, source.name)
