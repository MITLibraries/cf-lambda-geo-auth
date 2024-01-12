# lambda_edge.py

The name of the base file for the CloudFront-integrated Lambda@Edge functions should be `lambda_edge.py`. This is what is configured by default in the Terraform repository that manages the Lambda function deployment:

```terraform
resource "aws_lambda_function" "lambda_edge_geo_auth" {
  .
  .
  .
  handler                        = "lambda_edge.lambda_handler"
  .
  .
  .
}
```

If, for any reason, the name of the base file here changes, the Terraform code must also be updated.

## Repo setup (delete this section and above after initial function setup)

1. Update license if needed (check app-specific dependencies for licensing terms).
1. Check Github repository settings:
   - Confirm repo branch protection settings are correct (see [dev docs](https://mitlibraries.github.io/guides/basics/github.html) for details)
   - Confirm that all of the following are enabled in the repo's code security and analysis settings:
      - Dependabot alerts
      - Dependabot security updates
      - Secret scanning

## Development

- To preview a list of available Makefile commands: `make help`
- To install with dev dependencies: `make install`
- To update dependencies: `make update`
- To run unit tests: `make test`
- To lint the repo: `make lint`

## Running locally
