import jwt
import datetime


def create_jwt(logger, project_id, private_key_file, algorithm):
    """
    Creates a JWT (https://jwt.io) to establish an MQTT connection.
    Args:
        logger: logger
        project_id: The cloud project ID this device belongs to
        private_key_file: A path to a file containing either an RSA256 or
             ES256 private key.
        algorithm: The encryption algorithm to use. Either 'RS256' or 'ES256'
    Returns:
        A JWT generated from the given project_id and private key, which
        expires in 20 minutes. After 20 minutes, your client will be
        disconnected, and a new JWT will have to be generated.
    Raises:
        ValueError: If the private_key_file does not contain a known key.
    """

    # The time that the token was issued at
    jwt_iat = datetime.datetime.utcnow()
    # The time the token expires.
    jwt_exp = jwt_iat + datetime.timedelta(minutes=20)

    token = {
        "iat": jwt_iat,
        "exp": jwt_exp,
        # The audience field should always be set to the GCP project id.
        "aud": project_id,
    }

    # Read the private key file.
    with open(private_key_file, "r") as f:
        private_key = f.read()

    logger.debug("Creating JWT using {} from private key file {}".format(
        algorithm, private_key_file
    ))

    return jwt.encode(token, private_key, algorithm=algorithm), jwt_exp
