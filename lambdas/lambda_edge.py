import logging
import urllib.parse

import boto3
import jwt


def parse_cookies(headers):
    parsed_cookie = {}
    if headers.get("cookie"):
        for cookie in headers["cookie"][0]["value"].split(";"):
            if cookie:
                parts = cookie.split("=")
                parsed_cookie[parts[0].strip()] = parts[1].strip()
    return parsed_cookie.get("mitlcdnauthjwt", "")


def validate_jwt(jwt, jwt_secret):
    if jwt == "":
        return False

    decoded = decode_jwt(jwt, jwt_secret)
    if decoded == "invalid":
        return "invalid"

    if decoded == "expired":
        return "expired"

    # valid JWT: user is legit for general access. This is where
    # apps needing specific user auth and not general user auth would
    # need to check the user that was returned is authorized, not just
    # authenticated. For our initial purposes, authenticated is all we
    # will be checking for
    return "valid"


def decode_jwt(usertoken, jwt_secret):
    try:
        jwt.decode(usertoken, jwt_secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        # Signature has expired
        logging.exception("JWT token error: jwt.ExpiredSignatureError")
        return "expired"
    except jwt.InvalidSignatureError:
        # Signature is invaid
        logging.exception("JWT token error: jwt.InvalidSignatureError")
        return "invalid"
    except jwt.DecodeError:
        # Bogus JWT token
        logging.exception("JWT token error: jwt.DecodeError")
        return "invalid"
    return "valid"


def handler(event, _context):
    request = event["Records"][0]["cf"]["request"]
    headers = request["headers"]

    """
    Check for session-id in request cookie in viewer-request event,
    if session-id is absent, redirect the user to sign in page with original
    request sent as redirect_url in query params.
    """

    client = boto3.client("ssm", region_name="us-east-1")

    ssm_params = client.get_parameters_by_path(
        Path="/apps/cf-lambda-geo-auth/", WithDecryption=False
    )

    logging.info(ssm_params)

    for param in ssm_params["Parameters"]:
        if param["Name"] == "/apps/cf-lambda-geo-auth/jwt-secret":
            jwt_secret = param["Value"]
        if param["Name"] == "/apps/cf-lambda-geo-auth/auth-url":
            auth_url = param["Value"]

    # Check for session-id in cookie, if present, then proceed with request
    jwt = parse_cookies(headers)

    parsed_jwt = validate_jwt(jwt, jwt_secret)

    if parsed_jwt == "valid":
        # holy heck a valid user
        logging.info("valid user!")
        return request

    logging.info("need auth")
    # URI encode the original request to be sent as redirect_url in query params
    redirect_url = "https://{}{}?{}".format(
        headers["host"][0]["value"], request["uri"], request["querystring"]
    )
    encoded_redirect_url = urllib.parse.quote_plus(redirect_url.encode("utf-8"))

    return {
        "status": "302",
        "statusDescription": "Found",
        "headers": {
            "location": [
                {
                    "key": "Location",
                    "value": f"{auth_url}?cdn_resource={encoded_redirect_url}",
                }
            ]
        },
    }
