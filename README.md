# lambda_edge.py

The name of the base file for the CloudFront-integrated Lambda@Edge functions should be `lambda_edge.py`. This is what is configured by default in the Terraform repository that manages the Lambda function deployment:

```terraform
resource "aws_lambda_function" "lambda_edge_geo_auth" {
  .
  .
  .
  handler                        = "lambda_edge.handler"
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

## Context

This lambda@edge function runs during the `Viewer request` phase of a [CloudFront request](https://docs.aws.amazon.com/lambda/latest/dg/lambda-edge.html). This is important as we don't want cached versions of a request being sent to unauthenticated users which would happen if we instead ran in the `Origin request` phase once one authenticated user requested something.

This function checks for authenticated users by looking for a valid JWT token in a domain cookie. That cookie gets set by a separate application which is responsible for Touchstone authentication and JWT creation. The [user flow](https://github.com/MITLibraries/cdn-auth-geo?tab=readme-ov-file#how-does-this-application-integrate-with-others) is documented in that repository.

It is important to note that because we are checking for domain cookies, the CDN Auth Geo application and the CloudFront distribution must both have the same domain for the tier you are testing. In other words, for staging and dev1 tiers `*.mitlibrary.net` and for prod `*.libraries.mit.edu`.

## Development

- To preview a list of available Makefile commands: `make help`
- To install with dev dependencies: `make install`
- To update dependencies: `make update`
- To run unit tests: `make test`
- To lint the repo: `make lint`

## Running locally

Because of the nature of this lambda and it's tight coupling with CloudFront Events, it is generally easier to run it in
Dev1 and make changes directly in the Lambda editor, deploy it, and update the CloudFront distro to see changes. Yes,
that is unfortunate.

It should be possible to run moto in server mode to mock a CloudFront distribution to allow for true local development
of this function. If you figure that out, please update these docs!

