# 1. Select the CDN Geo-Auth Lambda Handler Name

Date: 2024-01-23

## Status

Accepted

## Context

Per the AWS documentation for [Lambda function handlers in Python](https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html?icmpid=docs_lambda_help), we need to ensure that what Terraform defines for the handler when it create the Lambda function matches up with what the developer uses for a file name and function name in the dependent application repository.

See ADR#9 in [mitlib-tf-workloads-libraries-website](https://github.com/MITLibraries/mitlib-tf-workloads-libraries-website) which says the exact same thing.

See the conversation on [GDT-106](https://mitlibraries.atlassian.net/browse/GDT-106) for further details.

## Decision

1. The "custom domain" Lambda function handler is `handler`.
2. The "custom domain" Lambda function filename in which the handler function lives is `lambda_edge.py`.

The name of the handler that is used in the `resource "aws_lambda_function" "lambda_edge_geo_auth" {}` resource is `lambda_edge.handler`.

## Consequences

If anyone decides to rename Python files in this repo, then the definition of the Lambda function in the [mitlib-tf-workloads-libraries-website](https://github.com/MITLibraries/mitlib-tf-workloads-libraries-website) repo might need to be udpated.
