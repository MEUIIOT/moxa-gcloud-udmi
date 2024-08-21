import os
import sys


# import datetime
#
# from cryptography import x509
# from cryptography.hazmat.primitives import serialization as crypto_serialization, hashes, serialization
# from cryptography.hazmat.primitives.asymmetric import rsa
# from cryptography.hazmat.backends import default_backend as crypto_default_backend
# from cryptography.x509.oid import NameOID


def get_google_root_ca(resources_path):
    """
    Get Google IoT Core root cert
    """
    return os.path.join(resources_path, "roots.pem")


def get_gateway_private_key(logger, udmi_site_model_path, gateway_id):
    """
    Get private key file, for the Google IoT Core authentication
    Args:
        logger: Logger
        udmi_site_model_path: UDMI Site Model path
        gateway_id: ID of Google Iot Core gateway device
    Returns:
        Gateway private key
    """
    udmi_site_model_path = os.path.join(udmi_site_model_path, "devices", gateway_id)

    private_key_file_path = os.path.join(udmi_site_model_path, "rsa_private.pem")
    if os.path.exists(private_key_file_path):
        return private_key_file_path, "RS256"

    private_key_file_path = os.path.join(udmi_site_model_path, "ec_private.pem")
    if os.path.exists(private_key_file_path):
        return private_key_file_path, "ES256"

    logger.error(
        f"Private key not found! Please make sure that either 'rsa_private.pem' or 'ec_private.pem' file is at '{udmi_site_model_path}' path")
    sys.exit(1)

# def _generate_rsa_key():
#     key = rsa.generate_private_key(
#         backend=crypto_default_backend(),
#         public_exponent=65537,
#         key_size=2048
#     )
#     return key
#
#
# def _generate_private_key(key):
#     private_key = key.private_bytes(
#         crypto_serialization.Encoding.PEM,
#         crypto_serialization.PrivateFormat.PKCS8,
#         crypto_serialization.NoEncryption())
#     return private_key
#
#
# def _generate_public_key(key):
#     public_key = key.public_key().public_bytes(
#         crypto_serialization.Encoding.PEM,
#         crypto_serialization.PublicFormat.PKCS1
#     )
#     return "public", public_key
#
#
# def _generate_certificate(key):
#     subject = issuer = x509.Name([
#         x509.NameAttribute(NameOID.COUNTRY_NAME, u"DE"),
#         x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"Bavaria"),
#         x509.NameAttribute(NameOID.LOCALITY_NAME, u"Munich"),
#         x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"MOXA Inc."),
#         x509.NameAttribute(NameOID.COMMON_NAME, u"moxa.com"),
#     ])
#     cert = x509.CertificateBuilder().subject_name(
#         subject
#     ).issuer_name(
#         issuer
#     ).public_key(
#         key.public_key()
#     ).serial_number(
#         x509.random_serial_number()
#     ).not_valid_before(
#         datetime.datetime.utcnow()
#     ).not_valid_after(
#         # Our certificate will be valid for 10 days
#         datetime.datetime.utcnow() + datetime.timedelta(days=30)
#     ).add_extension(
#         x509.SubjectAlternativeName([x509.DNSName(u"localhost")]),
#         critical=False,
#         # Sign our certificate with our private key
#     ).sign(key, hashes.SHA256())
#     return "cert", cert.public_bytes(serialization.Encoding.PEM)
#
#
# def generate_key_files(logger, algorithm="RSA_X509", regenerate=False):
#     logger.info("Generating private and public keys")
#
#     resources_path = os.environ['GOOGLE_IOT_CORE_GATEWAY_RESOURCES_PATH']
#     private_key_file_path = os.path.join(resources_path, "rsa_private.pem")
#
#     if not regenerate and os.path.exists(private_key_file_path):
#         logger.info("Keys exists, skipping")
#         if algorithm == "RSA":
#             return private_key_file_path, os.path.join(resources_path, "rsa_public.pem")
#         else:
#             return private_key_file_path, os.path.join(resources_path, "rsa_cert.pem")
#
#     key = _generate_rsa_key()
#
#     private_key = _generate_private_key(key)
#
#     if algorithm == "RSA":
#         name, content = _generate_public_key(key)
#     else:
#         name, content = _generate_certificate(key)
#
#     public_key_file_path = "{}/rsa_{}.pem".format(resources_path, name)
#
#     with open(private_key_file_path, 'wb') as content_file:
#         content_file.write(private_key)
#     with open(public_key_file_path, "wb") as content_file:
#         content_file.write(content)
#
#     return private_key_file_path, public_key_file_path
