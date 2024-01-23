from lambdas import lambda_edge


def test_lambda_edge():
    assert lambda_edge.handler({}) == "You have successfully called this lambda!"
