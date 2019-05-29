"""Cloud Functions to send Billing Notifications to Slack."""

import base64
import datetime
import json
import os
import slackclient


SLACK_API_TOKEN = os.environ.get('SLACK_API_TOKEN')
SLACK_CHANNEL = os.environ.get('SLACK_CHANNEL')


def _create_budget_notification(context_data, attributes, data):
    """Return a budget notification."""
    # process timestamp
    cost_interval_start = _process_timestamp(data['costIntervalStart'])

    notification = {
        'alert_threshold_exceeded': data.get('alertThresholdExceeded'),
        'billing_account_id': attributes['billingAccountId'],
        'budget_amount': data['budgetAmount'],
        'budget_amount_type': data['budgetAmountType'],
        'budget_display_name': data['budgetDisplayName'],
        'budget_id': attributes['budgetId'],
        'cost_amount': data['costAmount'],
        'cost_interval_start': cost_interval_start,
        'currency_code': data['currencyCode'],
        'event_id': context_data['eventId'],
        'event_type': context_data['eventType'],
        'schema_version': attributes['schemaVersion'],
        'timestamp': context_data['eventTimestamp'],
    }
    return notification


def _notify_slack(notification):
    """Send a notification to slack."""
    # create message to send to slack
    message = "Budget Threshold Exceeded for Budget: *%s*:\n"
    message += "> Billing Account ID: `%s`\n"
    message += "> Budget ID: `%s`\n"
    message += "> Amount: `$%s` out of `$%s` represents `%s` of budget\n"
    message += "> Exceeded Threshold: `%s`\n"
    message += "Console: %s"

    percentage = (notification['cost_amount'] / notification['budget_amount']) * 100
    url = 'https://console.cloud.google.com/billing/%s/budgets/%s' % (
        notification['billing_account_id'],
        notification['budget_id'],
    )

    # add in data from notification
    text = message % (
        notification['budget_display_name'],
        notification['billing_account_id'],
        notification['budget_id'],
        notification['cost_amount'],
        notification['budget_amount'],
        '%s%%' % (round(percentage, 2)),
        notification['alert_threshold_exceeded'],
        url,
    )

    sc = slackclient.SlackClient(SLACK_API_TOKEN)

    sc.api_call(
        "chat.postMessage",
        channel=SLACK_CHANNEL,
        text=text,
    )


def _process_pubsub_context(context):
    """Process PubSub event context."""
    # if no context, return without doing anything
    if not context:
        return {}

    # process timestamp
    timestamp = _process_timestamp(context.timestamp)

    data = {
        'eventId': context.event_id,
        'eventType': context.event_type,
        'eventTimestamp': timestamp,
        'resourceName': context.resource.get('name'),
        'resourceService': context.resource.get('service'),
        'resourceType': context.resource.get('type'),
    }

    return data


def _process_pubsub_message(message):
    """Process Billing Notification PubSub message data."""
    # get message attributes and data
    attributes = message.get('attributes')
    message_data = message.get('data')

    # get base64-encoded message data as a string
    json_string = base64.b64decode(message_data).decode('utf-8')

    # convert string to json
    data = json.loads(json_string)

    return attributes, data


def _process_timestamp(datestring):
    """Process a timestamp string and return a datetime."""
    dateformat = '%Y-%m-%dT%H:%M:%SZ'
    if '.' in datestring:
        dateformat = '%Y-%m-%dT%H:%M:%S.%fZ'
    return datetime.datetime.strptime(datestring, dateformat)


def billing_pubsub_to_slack(message, context):
    """Process a single billing notification."""
    # process pubsub event context
    context_data = _process_pubsub_context(context)

    # process pubsub message
    attributes, data = _process_pubsub_message(message)

    # create a dict of all notification data
    notification = _create_budget_notification(
        context_data,
        attributes,
        data
    )

    # do nothing if we haven't exceeded any threshold
    if not notification['alert_threshold_exceeded']:
        return

    # notify slack
    _notify_slack(notification)


if __name__ == "__main__":

    example = {
        'alert_threshold_exceeded': 1.0,
        'billing_account_id': '00A539-93294F-AC9B6F',
        'budget_amount': 500.0,
        'budget_amount_type': 'SPECIFIED_AMOUNT',
        'budget_display_name': 'My Really Fancy Budget',
        'budget_id': '40e0023d-aefd-4e26-a58d-11c7abd3432c',
        'cost_amount': 3486.03,
        'cost_interval_start': datetime.datetime(2019, 5, 1, 7, 0),
        'currency_code': 'USD',
        'event_id': '565618620270615',
        'event_type': 'google.pubsub.topic.publish',
        'schema_version': '1.0',
        'timestamp': datetime.datetime(2019, 5, 28, 22, 50, 6, 143000)
    }
    _notify_slack(example)