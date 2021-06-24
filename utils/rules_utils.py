import operator

from models.models import CampaignRule, db, SourceRule


def set_campaign_rule_fields(rule_dict):
    campaign_rule = CampaignRule()
    campaign_rule.conditions = rule_dict['conditions']
    campaign_rule.ts_id = rule_dict['ts']
    campaign_rule.param1 = rule_dict['param1']
    campaign_rule.sign1 = rule_dict['sign1']
    campaign_rule.factor_var1 = rule_dict['factor_var1']
    campaign_rule.param2 = rule_dict['param2']
    campaign_rule.sign2 = rule_dict['sign2']
    campaign_rule.factor_var2 = rule_dict['factor_var2']
    campaign_rule.param3 = rule_dict['param3']
    campaign_rule.sign3 = rule_dict['sign3']
    campaign_rule.factor_var3 = rule_dict['factor_var3']
    campaign_rule.param4 = rule_dict['param4']
    campaign_rule.sign4 = rule_dict['sign4']
    campaign_rule.factor_var4 = rule_dict['factor_var4']
    campaign_rule.days = rule_dict['days']
    campaign_rule.action = rule_dict['action']

    campaign_rule.campaign_name = rule_dict['name']
    if not campaign_rule.campaign_name or campaign_rule.campaign_name == '*':
        campaign_rule.campaign_name = '*'

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

    try:
        campaign_rule.factor1 = float(rule_dict['factor1'])
    except ValueError:
        campaign_rule.factor1 = 0

    try:
        campaign_rule.factor2 = float(rule_dict['factor2'])
    except ValueError:
        campaign_rule.factor2 = 0

    try:
        campaign_rule.factor3 = float(rule_dict['factor3'])
    except ValueError:
        campaign_rule.factor3 = 0

    try:
        campaign_rule.factor4 = float(rule_dict['factor4'])
    except ValueError:
        campaign_rule.factor4 = 0

    return campaign_rule


def set_source_rule_fields(rule_dict):
    source_rule = SourceRule()
    source_rule.conditions = rule_dict['conditions']
    source_rule.ts_id = rule_dict['ts']
    source_rule.param1 = rule_dict['param1']
    source_rule.sign1 = rule_dict['sign1']
    source_rule.factor_var1 = rule_dict['factor_var1']
    source_rule.param2 = rule_dict['param2']
    source_rule.sign2 = rule_dict['sign2']
    source_rule.factor_var2 = rule_dict['factor_var2']
    source_rule.param3 = rule_dict['param3']
    source_rule.sign3 = rule_dict['sign3']
    source_rule.factor_var3 = rule_dict['factor_var3']
    source_rule.param4 = rule_dict['param4']
    source_rule.sign4 = rule_dict['sign4']
    source_rule.factor_var4 = rule_dict['factor_var4']
    source_rule.days = rule_dict['days']
    source_rule.action = rule_dict['action']

    source_rule.source_name = rule_dict['name']
    if not source_rule.source_name or source_rule.source_name == '*':
        source_rule.source_name = '*'

    source_rule.campaign_name = rule_dict['campaign_name']
    if not source_rule.campaign_name or source_rule.campaign_name == '*':
        source_rule.campaign_name = '*'

    try:
        source_rule.value1 = float(rule_dict['value1'])
    except ValueError:
        source_rule.value1 = 0

    try:
        source_rule.value2 = float(rule_dict['value2'])
    except ValueError:
        source_rule.value2 = 0

    try:
        source_rule.value3 = float(rule_dict['value3'])
    except ValueError:
        source_rule.value3 = 0

    try:
        source_rule.value4 = float(rule_dict['value4'])
    except ValueError:
        source_rule.value4 = 0

    try:
        source_rule.factor1 = float(rule_dict['factor1'])
    except ValueError:
        source_rule.factor1 = 0

    try:
        source_rule.factor2 = float(rule_dict['factor2'])
    except ValueError:
        source_rule.factor2 = 0

    try:
        source_rule.factor3 = float(rule_dict['factor3'])
    except ValueError:
        source_rule.factor3 = 0

    try:
        source_rule.factor4 = float(rule_dict['factor4'])
    except ValueError:
        source_rule.factor4 = 0

    return source_rule


def save_rule_to_db(rule):
    db.session.add(rule)
    db.session.commit()


def get_comparison_operator(operator_str):
    operators = [
        (operator.eq, "=="),
        (operator.lt, "<"),
        (operator.gt, ">"),
        (operator.ge, ">="),
        (operator.le, "<="),
    ]

    for op, label in operators:
        if operator_str == label:
            return op

    return None


def get_campaign_action(action_str, api):
    actions = [
        (api.start_campaign, "resume"),
        (api.stop_campaign, "pause")
    ]

    for action, label in actions:
        if action_str == label:
            return action

    return None


def get_source_action(action_str, api):
    actions = [
        (api.add_sources_to_blacklist, "pause"),
        (api.remove_sources_from_blacklist, "resume")
    ]

    for action, label in actions:
        if action_str == label:
            return action

    return None
