import json
import logging
from datetime import datetime, timedelta

import requests
from requests import HTTPError
from sqlalchemy.sql.expression import and_

from models.models import Campaign, Source, DailyCampaign, CampaignRule, DailySource, SourceRule, db, PausedSource
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

            stats_url = f'{stats_url}?group_by[]=publisher&group_by[]=date&group_by[]=creative_id&date_start={start_date}&date_finish={end_date}&campaign_id={campaign_name}'
        else:
            stats_url = f'{stats_url}?group_by[]=publisher&group_by[]=date&group_by[]=creative_id&campaign_id={campaign_name}'

        return stats_url

    def get_campaign_status_url(self):
        status_url = self.config['ungads_urls']['campaign_status']
        ungads_api_key = self.config["api_keys"]["ungads"]
        status_url = status_url.replace('[API_KEY]', ungads_api_key)
        return status_url

    def parse_campaigns_json(self, json, ts_id):
        campaigns = []
        if json:
            for element in json:
                try:
                    name = element['name']

                    if not name.isdigit():
                        continue

                    revenue = float(element['revenue'])
                    campaign = Campaign(name, revenue, ts_id)
                    campaigns.append(campaign)
                except:
                    logging.error('Parsing campaigns json error')

        return campaigns

    def parse_campaign_cost_json(self, ts_id, json):
        if not json:
            return 0

        if int(ts_id) == self.config['traffic_source_ids']['push_house']:
            return float(json[0]['cost'])
        else:
            return float(json[0]['spent_advertiser'])

    def parse_campaign_status_json(self, ts_id, json):
        if not json or int(ts_id) == self.config['traffic_source_ids']['push_house']:
            return 'undefined'

        return json[next(iter(json))]['status']

    def parse_sources_json(self, json, ts_id):
        sources = []
        campaign_name = ''
        if json:
            for element in json:
                try:
                    if element['level'] == '1':
                        campaign_name = element['name']
                        continue

                    name = element['name']
                    revenue = float(element['revenue'])
                    source = Source(name, campaign_name, revenue, ts_id)
                    sources.append(source)
                except:
                    logging.error('Parsing sources json error')

        return sources

    def parse_sources_costs_json(self, campaign_name, sources, ts_id, json):
        if int(ts_id) == self.config['traffic_source_ids']['push_house']:
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
                cost = self.parse_campaign_cost_json(ts_id, response.json())
                logging.info(f'Fetched cost {cost} for campaign {campaign.name} from ts {ts_id}')
                campaign.cost = cost

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
            except HTTPError as http_err:
                logging.error(f'HTTP error occurred: {http_err}')  # Python 3.6
            except Exception as err:
                logging.error(f'Other error occurred: {err}')  # Python 3.6
            else:
                if response:
                    status = self.parse_campaign_status_json(ts_id, response.json())
                    campaign.status = status

        return campaigns

    def get_campaigns_profit(self, campaigns):
        for campaign in campaigns:
            campaign.profit = campaign.revenue - campaign.cost

        return campaigns

    def get_campaigns(self, ts_id, start_date=None, end_date=None):
        if start_date and end_date:
            try:
                campaigns = self.get_campaigns_revenues(ts_id, start_date, end_date)
                campaigns = self.get_campaigns_costs(campaigns, ts_id, start_date, end_date)
                campaigns = self.get_campaigns_statuses(campaigns, ts_id)
            except Exception as e:
                logging.error(f'{e}. Trying again')
                campaigns = self.get_campaigns_revenues(ts_id, start_date, end_date)
                campaigns = self.get_campaigns_costs(campaigns, ts_id, start_date, end_date)
        else:
            campaigns = self.get_campaigns_revenues(ts_id)
            campaigns = self.get_campaigns_costs(campaigns, ts_id)
            campaigns = self.get_campaigns_statuses(campaigns, ts_id)

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
            logging.info(f'Cleared blacklist')
            print(response.json())

    def start_campaign(self, campaign_name, ts_id):
        try:
            url = self.get_campaign_start_url(campaign_name, ts_id)

            response = requests.get(url)

            # If the response was successful, no Exception will be raised
            response.raise_for_status()
        except HTTPError as http_err:
            logging.error(f'HTTP error occurred: {http_err}')  # Python 3.6
        except Exception as err:
            logging.error(f'Other error occurred: {err}')  # Python 3.6
        else:
            logging.info('Start campaign ' + campaign_name)
            print(response.content)

    def stop_campaign(self, campaign_name, ts_id):
        try:
            url = self.get_campaign_stop_url(campaign_name, ts_id)

            response = requests.get(url)

            # If the response was successful, no Exception will be raised
            response.raise_for_status()
        except HTTPError as http_err:
            logging.error(f'HTTP error occurred: {http_err}')  # Python 3.6
        except Exception as err:
            logging.error(f'Other error occurred: {err}')  # Python 3.6
        else:
            logging.info('Stop campaign ' + campaign_name)
            print(response.content)

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
                logging.info(f'Source {sources_names} added to blacklist')
                print(response.text)

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
                print(response.text)

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
            else:
                campaigns = DailyCampaign.query.filter(
                    DailyCampaign.fetched_at >= now - timedelta(days=rule.days)).all()

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
                sources = DailySource.query.filter(
                    and_(
                        DailySource.name == rule.source_name,
                        DailySource.campaign_name == rule.campaign_name,
                        DailySource.fetched_at >= now - timedelta(days=rule.days))
                ).all()
            else:
                sources = DailySource.query.filter(
                    and_(
                        DailySource.campaign_name == rule.campaign_name,
                        DailySource.fetched_at >= now - timedelta(days=rule.days))
                ).all()

            unique_sources_names = set()
            [unique_sources_names.add(source.name) for source in sources if source.name not in unique_sources_names]

            unique_campaigns_names = set()
            [unique_campaigns_names.add(source.campaign_name) for source in sources if
             source.campaign_name not in unique_campaigns_names]

            sources_stats_list = []
            for campaign_name in unique_campaigns_names:
                for name in unique_sources_names:
                    source_stat = Source(name, campaign_name, 0, 0)
                    source_stat.cost = 0
                    source_stat.profit = 0

                    for source in sources:
                        if source.name == name and source.campaign_name == campaign_name:
                            source_stat.traffic_source = source.traffic_source
                            source_stat.revenue += source.revenue
                            source_stat.cost += source.cost
                            source_stat.profit += source.profit

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
                action = get_source_action(getattr(rule, 'action'), self)
                action(campaign_name, appropriate_sources, traffic_source)
