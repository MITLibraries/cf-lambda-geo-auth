from datetime import datetime, timedelta, timezone

import boto3
import jwt
import pytest
from moto import mock_aws

from lambdas import lambda_edge


@pytest.fixture
def jwt_secret():
    return "secret"


@pytest.fixture
def valid_token(jwt_secret):
    return jwt.encode(
        {
            "user": "fakeuser",
            "exp": datetime.now(tz=timezone.utc) + timedelta(minutes=1),
            "nbf": datetime.now(tz=timezone.utc) - timedelta(minutes=5),
        },
        jwt_secret,
        algorithm="HS256",
    )


@pytest.fixture
def invalid_signature_token(jwt_secret):
    return jwt.encode(
        {
            "user": "fakeuser",
            "exp": datetime.now(tz=timezone.utc) + timedelta(minutes=1),
            "nbf": datetime.now(tz=timezone.utc) - timedelta(minutes=5),
        },
        "wrong_secret",
        algorithm="HS256",
    )


@pytest.fixture
def expired_token(jwt_secret):
    return jwt.encode(
        {
            "user": "fakeuser",
            "exp": datetime.now(tz=timezone.utc) - timedelta(minutes=10),
            "nbf": datetime.now(tz=timezone.utc) - timedelta(minutes=5),
        },
        jwt_secret,
        algorithm="HS256",
    )


@pytest.fixture
def invalid_token(jwt_secret):
    return "asdf1234"


def test_decode_jwt_valid_token(valid_token, jwt_secret):
    assert lambda_edge.decode_jwt(valid_token, jwt_secret) == "valid"


def test_decode_jwt_invalid_token(invalid_token, jwt_secret):
    assert lambda_edge.decode_jwt(invalid_token, jwt_secret) == "invalid"


def test_decode_jwt_expired_token(expired_token, jwt_secret):
    assert lambda_edge.decode_jwt(expired_token, jwt_secret) == "expired"


def test_decode_jwt_invalid_signature(invalid_signature_token, jwt_secret):
    assert lambda_edge.decode_jwt(invalid_signature_token, jwt_secret) == "invalid"


@pytest.fixture
def cookie_no_jwt():
    return ""


@pytest.fixture
def cookie_valid_jwt(valid_token):
    return valid_token


@pytest.fixture
def cookie_expired_jwt(expired_token):
    return expired_token


@pytest.fixture
def cookie_invalid_jwt(invalid_token):
    return invalid_token


def test_validate_jwt_no_jwt(cookie_no_jwt, jwt_secret):
    assert lambda_edge.validate_jwt(cookie_no_jwt, jwt_secret) is False


def test_validate_jwt_valid_jwt(cookie_valid_jwt, jwt_secret):
    assert lambda_edge.validate_jwt(cookie_valid_jwt, jwt_secret) == "valid"


def test_validate_jwt_expired_jwt(cookie_expired_jwt, jwt_secret):
    assert lambda_edge.validate_jwt(cookie_expired_jwt, jwt_secret) == "expired"


def test_validate_jwt_invalid_jwt(cookie_invalid_jwt, jwt_secret):
    assert lambda_edge.validate_jwt(cookie_invalid_jwt, jwt_secret) == "invalid"


@pytest.fixture
def headers_with_cookies(valid_token):
    return {
        "host": [{"key": "Host", "value": "d123.cf.net"}],
        "cookie": [
            {
                "key": "Cookie",
                "value": f"mitlcdnauthjwt={valid_token}; AnotherOne=A; X-Name=B",
            }
        ],
    }


def test_parse_cookies_present(headers_with_cookies, valid_token):
    assert lambda_edge.parse_cookies(headers_with_cookies) == valid_token


@pytest.fixture
def headers_without_cookies():
    return {
        "host": [{"key": "Host", "value": "d123.cf.net"}],
    }


@pytest.fixture
def headers_with_irrelvant_cookies():
    return {
        "host": [{"key": "Host", "value": "d123.cf.net"}],
        "cookie": [
            {
                "key": "Cookie",
                "value": "AnotherOne=A; X-Experiment-Name=B",
            }
        ],
    }


def test_parse_cookies_missing(headers_without_cookies):
    assert lambda_edge.parse_cookies(headers_without_cookies) == ""


def test_parse_cookies_missing_relevant(headers_with_irrelvant_cookies):
    assert lambda_edge.parse_cookies(headers_with_irrelvant_cookies) == ""


@pytest.fixture
def event_happy_path(valid_token):
    return {
        "Records": [
            {
                "cf": {
                    "config": {"distributionId": "EXAMPLE"},
                    "request": {
                        "uri": "/test",
                        "method": "GET",
                        "querystring": "foo=bar",
                        "headers": {
                            "host": [{"key": "Host", "value": "d123.cf.net"}],
                            "cookie": [
                                {
                                    "key": "Cookie",
                                    "value": f"mitlcdnauthjwt={valid_token};"
                                    "AnotherOne=A; X-Experiment-Name=B",
                                }
                            ],
                        },
                    },
                }
            }
        ]
    }


def test_handler_happy_path(event_happy_path):
    with mock_aws():
        client = boto3.client("ssm", region_name="us-east-1")
        client.put_parameter(
            Name="/apps/cf-lambda-geo-auth/jwt-secret", Value="secret", Type="String"
        )
        client.put_parameter(
            Name="/apps/cf-lambda-geo-auth/auth-url",
            Value="https://example.com/hallo",
            Type="String",
        )

        assert (
            lambda_edge.handler(event_happy_path, "fake context")
            == event_happy_path["Records"][0]["cf"]["request"]
        )


@pytest.fixture
def event_need_auth():
    return {
        "Records": [
            {
                "cf": {
                    "config": {"distributionId": "EXAMPLE"},
                    "request": {
                        "uri": "/test",
                        "method": "GET",
                        "querystring": "foo=bar",
                        "headers": {"host": [{"key": "Host", "value": "d123.cf.net"}]},
                    },
                }
            }
        ]
    }


def test_handler_need_auth(event_need_auth):
    with mock_aws():
        client = boto3.client("ssm", region_name="us-east-1")
        client.put_parameter(
            Name="/apps/cf-lambda-geo-auth/jwt-secret", Value="secret", Type="String"
        )
        client.put_parameter(
            Name="/apps/cf-lambda-geo-auth/auth-url",
            Value="https://example.com/hallo",
            Type="String",
        )

        assert lambda_edge.handler(event_need_auth, "fake context") == {
            "status": "302",
            "statusDescription": "Found",
            "headers": {
                "location": [
                    {
                        "key": "Location",
                        "value": "https://example.com/hallo?cdn_resource=https%3A%2F%2Fd123.cf.net%2Ftest%3Ffoo%3Dbar",
                    }
                ]
            },
        }


@pytest.fixture
def event_expired_auth(expired_token):
    return {
        "Records": [
            {
                "cf": {
                    "config": {"distributionId": "EXAMPLE"},
                    "request": {
                        "uri": "/test",
                        "method": "GET",
                        "querystring": "foo=bar",
                        "headers": {
                            "host": [{"key": "Host", "value": "d123.cf.net"}],
                            "cookie": [
                                {
                                    "key": "Cookie",
                                    "value": f"mitlcdnauthjwt={expired_token};"
                                    "AnotherOne=A; X-Experiment-Name=B",
                                }
                            ],
                        },
                    },
                }
            }
        ]
    }


def test_handler_expired_auth(event_expired_auth):
    with mock_aws():
        client = boto3.client("ssm", region_name="us-east-1")
        client.put_parameter(
            Name="/apps/cf-lambda-geo-auth/jwt-secret", Value="secret", Type="String"
        )
        client.put_parameter(
            Name="/apps/cf-lambda-geo-auth/auth-url",
            Value="https://example.com/hallo",
            Type="String",
        )

        assert lambda_edge.handler(event_expired_auth, "fake context") == {
            "status": "302",
            "statusDescription": "Found",
            "headers": {
                "location": [
                    {
                        "key": "Location",
                        "value": "https://example.com/hallo?cdn_resource="
                        "https%3A%2F%2Fd123.cf.net%2Ftest%3Ffoo%3Dbar",
                    }
                ]
            },
        }


@pytest.fixture
def event_invalid_auth(invalid_signature_token):
    return {
        "Records": [
            {
                "cf": {
                    "config": {"distributionId": "EXAMPLE"},
                    "request": {
                        "uri": "/test",
                        "method": "GET",
                        "querystring": "foo=bar",
                        "headers": {
                            "host": [{"key": "Host", "value": "d123.cf.net"}],
                            "cookie": [
                                {
                                    "key": "Cookie",
                                    "value": f"mitlcdnauthjwt={invalid_signature_token};"
                                    "AnotherOne=A; X-Experiment-Name=B",
                                }
                            ],
                        },
                    },
                }
            }
        ]
    }


def test_handler_invalid_auth(event_invalid_auth):
    with mock_aws():
        client = boto3.client("ssm", region_name="us-east-1")
        client.put_parameter(
            Name="/apps/cf-lambda-geo-auth/jwt-secret", Value="secret", Type="String"
        )
        client.put_parameter(
            Name="/apps/cf-lambda-geo-auth/auth-url",
            Value="https://example.com/hallo",
            Type="String",
        )

        assert lambda_edge.handler(event_invalid_auth, "fake context") == {
            "status": "302",
            "statusDescription": "Found",
            "headers": {
                "location": [
                    {
                        "key": "Location",
                        "value": "https://example.com/hallo?cdn_resource=https%3A%2F%2Fd123.cf.net%2Ftest%3Ffoo%3Dbar",
                    }
                ]
            },
        }


def test_handler_missing_ssm_jwt_secret(event_happy_path):
    with mock_aws():
        client = boto3.client("ssm", region_name="us-east-1")
        client.put_parameter(
            Name="/apps/cf-lambda-geo-auth/auth-url",
            Value="https://example.com/hallo",
            Type="String",
        )
        with pytest.raises(RuntimeError):
            lambda_edge.handler(event_happy_path, "fake context")


def test_handler_missing_ssm_auth_url(event_happy_path):
    with mock_aws():
        client = boto3.client("ssm", region_name="us-east-1")
        client.put_parameter(
            Name="/apps/cf-lambda-geo-auth/jwt-secret", Value="secret", Type="String"
        )
        with pytest.raises(RuntimeError):
            lambda_edge.handler(event_happy_path, "fake context")
