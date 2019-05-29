#!/bin/sh

FUNCTION="billing_pubsub_to_slack"
PROJECT="broad-gcp-billing"
REGION="us-central1"
TOPIC="billingnotifications"

if [ -z "${SLACK_API_TOKEN}" ]; then
    echo "SLACK_API_TOKEN environment variable must be set to deploy."
    exit 1
fi

if [ -z "${SLACK_CHANNEL}" ]; then
    echo "SLACK_CHANNEL environment variable must be set to deploy."
    exit 1
fi

gcloud functions deploy ${FUNCTION} \
    --entry-point ${FUNCTION} \
    --memory=128MB \
    --project ${PROJECT} \
    --region ${REGION} \
    --runtime python37 \
    --set-env-vars SLACK_API_TOKEN=${SLACK_API_TOKEN},SLACK_CHANNEL=${SLACK_CHANNEL} \
    --trigger-event google.pubsub.topic.publish \
    --trigger-resource ${TOPIC}
