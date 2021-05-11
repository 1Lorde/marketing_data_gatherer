import logging
from datetime import datetime

import requests
from requests import HTTPError

from models.models import Campaign, Source


class ApiUtils:
    def __init__(self, config):
        self.config = config

    def get_binom_campaigns_url(self, start_date=None, end_date=None):
        campaigns_url = self.config['binom_urls']['campaigns']

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

    def get_binom_sources_url(self, start_date=None, end_date=None):
        sources_url = self.config['binom_urls']['sources']

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

    def parse_campaigns_json(self, json):
        campaigns = []
        for element in json:
            name = element['name']
            revenue = float(element['revenue'])
            campaign = Campaign(name, revenue)
            campaigns.append(campaign)

        return campaigns

    def parse_campaign_cost_json(self, json):
        return float(json[0]['cost'])

    def parse_sources_json(self, json):
        sources = []
        campaign_name = ''

        for element in json:
            if element['level'] == '1':
                campaign_name = element['name']
                continue

            name = element['name']
            revenue = float(element['revenue'])
            source = Source(name, campaign_name, revenue)
            sources.append(source)

        return sources

    def parse_sources_costs_json(self, campaign_name, sources, json):
        for element in json:
            for source in sources:
                if str(element['tname']) == source.name and source.campaign_name == campaign_name:
                    source.cost = float(element['cost'])

        return sources

    def get_campaigns_revenues(self, start_date=None, end_date=None):
        try:
            if start_date and end_date:
                url = self.get_binom_campaigns_url(start_date, end_date)
            else:
                url = self.get_binom_campaigns_url()

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
            return self.parse_campaigns_json(response.json())

    def get_campaigns_costs(self, campaigns, start_date=None, end_date=None):
        for campaign in campaigns:
            try:
                if start_date and end_date:
                    url = self.get_push_house_campaign_url(campaign.name, start_date, end_date)
                else:
                    url = self.get_push_house_campaign_url(campaign.name)

                response = requests.get(url)

                # If the response was successful, no Exception will be raised
                response.raise_for_status()
            except HTTPError as http_err:
                logging.error(f'HTTP error occurred: {http_err}')  # Python 3.6
            except Exception as err:
                logging.error(f'Other error occurred: {err}')  # Python 3.6
            else:
                cost = self.parse_campaign_cost_json(response.json())
                logging.info(f'Fetched cost {cost} for campaign {campaign.name}')
                campaign.cost = cost

        return campaigns

    def get_campaigns_profit(self, campaigns):
        for campaign in campaigns:
            campaign.profit = campaign.revenue - campaign.cost

        return campaigns

    def get_campaigns(self, start_date=None, end_date=None):
        if start_date and end_date:
            try:
                campaigns = self.get_campaigns_revenues(start_date, end_date)
                campaigns = self.get_campaigns_costs(campaigns, start_date, end_date)
            except Exception as e:
                logging.error(f'{e}. Trying again')
                campaigns = self.get_campaigns_revenues(start_date, end_date)
                campaigns = self.get_campaigns_costs(campaigns, start_date, end_date)
        else:
            campaigns = self.get_campaigns_revenues()
            campaigns = self.get_campaigns_costs(campaigns)

        campaigns = self.get_campaigns_profit(campaigns)

        return campaigns

    def get_sources_revenues(self, start_date=None, end_date=None):
        try:
            if start_date and end_date:
                url = self.get_binom_sources_url(start_date, end_date)
            else:
                url = self.get_binom_sources_url()

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

            return self.parse_sources_json(response.json())

    def get_sources_costs(self, campaigns, sources, start_date=None, end_date=None):
        for campaign in campaigns:
            try:
                if start_date and end_date:
                    url = self.get_push_house_sources_url(campaign.name, start_date, end_date)
                else:
                    url = self.get_push_house_sources_url(campaign.name)

                response = requests.get(url)

                # If the response was successful, no Exception will be raised
                response.raise_for_status()
            except HTTPError as http_err:
                logging.error(f'HTTP error occurred: {http_err}')  # Python 3.6
            except Exception as err:
                logging.error(f'Other error occurred: {err}')  # Python 3.6
            else:
                sources = self.parse_sources_costs_json(campaign.name, sources, response.json())
                logging.info(f'Fetched costs for sources with campaign_name {campaign.name}')

        return sources

    def get_sources_profit(self, sources):
        for source in sources:
            source.profit = source.revenue - source.cost

        return sources

    def get_sources(self, campaigns, start_date=None, end_date=None):
        try:
            sources = self.get_sources_revenues(start_date, end_date)
            sources = self.get_sources_costs(campaigns, sources, start_date, end_date)
            sources = self.get_sources_profit(sources)
        except Exception as e:
            logging.error(f'{e}. Trying again')
            sources = self.get_sources_revenues(start_date, end_date)
            sources = self.get_sources_costs(campaigns, sources, start_date, end_date)
            sources = self.get_sources_profit(sources)

        return sources
