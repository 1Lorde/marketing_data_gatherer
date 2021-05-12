import operator

from models.models import CampaignRule, db


def set_rules_field(rule_dict):
    campaign_rule = CampaignRule()
    campaign_rule.conditions = rule_dict['conditions']
    campaign_rule.campaign_name = rule_dict['name']
    campaign_rule.param1 = rule_dict['param1']
    campaign_rule.sign1 = rule_dict['sign1']
    campaign_rule.param2 = rule_dict['param2']
    campaign_rule.sign2 = rule_dict['sign2']
    campaign_rule.param3 = rule_dict['param3']
    campaign_rule.sign3 = rule_dict['sign3']
    campaign_rule.param4 = rule_dict['param4']
    campaign_rule.sign4 = rule_dict['sign4']
    campaign_rule.days = rule_dict['days']
    campaign_rule.action = rule_dict['action']

    try:
        campaign_rule.value1 = float(rule_dict['value1'])
    except ValueError:
        campaign_rule.value1 = 0

    try:
        campaign_rule.value2 = float(rule_dict['value2'])
    except ValueError:
        campaign_rule.value2 = 0

    try:
        campaign_rule.value3 = float(rule_dict['value3'])
    except ValueError:
        campaign_rule.value3 = 0

    try:
        campaign_rule.value4 = float(rule_dict['value4'])
    except ValueError:
        campaign_rule.value4 = 0

    return campaign_rule


def save_rule_to_db(rule):
    db.session.add(rule)
    db.session.commit()


def get_comparison_operator(operator_str):
    operators = [
        (operator.eq, "=="),
        (operator.lt, "<"),
        (operator.gt, ">"),
        (operator.ge, ">="),
        (operator.le, "=<"),
    ]

    for op, label in operators:
        if operator_str == label:
            return op

    return None


def get_action(action_str, api):
    actions = [
        (api.start_campaign, "resume"),
        (api.stop_campaign, "pause")
    ]

    for action, label in actions:
        if action_str == label:
            return action

    return None
