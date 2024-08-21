import io
import logging
import os

from google.api_core.exceptions import AlreadyExists
from google.cloud import iot_v1
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class GoogleIoTCoreManager:
    """
    This class is not used in the current implementation.
    UDMI tools instead are used to create registry, devices and gateway on the Google Iot Core.

    Manager is used to create registry, devices and gateway on the Google Iot Core.
    """

    def __init__(self, cloud_region, project_id, registry_id, gateway_id, algorithm):
        self.cloud_region = cloud_region
        self.project_id = project_id
        self.registry_id = registry_id
        self.gateway_id = gateway_id
        self.algorithm = algorithm

    def create_registry(self, pubsub_topic="device-events"):
        client = iot_v1.DeviceManagerClient()
        parent = f"projects/{self.project_id}/locations/{self.cloud_region}"

        if not pubsub_topic.startswith("projects/"):
            pubsub_topic = "projects/{}/topics/{}".format(self.project_id, pubsub_topic)

        body = {
            "event_notification_configs": [{"pubsub_topic_name": pubsub_topic}],
            "id": self.registry_id,
        }

        try:
            response = client.create_device_registry(
                request={"parent": parent, "device_registry": body}
            )
            logger.info("Created registry: {}".format(self.registry_id))
            return response
        except HttpError:
            logger.error("Error, registry '{}' not created".format(self.registry_id))
            raise
        except AlreadyExists:
            logger.info("Registry '{}' already exists, skipping".format(self.registry_id))

    def create_gateway(self, certificate_file):
        logger.info("Creating gateway: '{}'".format(self.gateway_id))

        exists = False
        client = iot_v1.DeviceManagerClient()

        parent = client.registry_path(self.project_id, self.cloud_region, self.registry_id)
        devices = list(client.list_devices(request={"parent": parent}))

        for device in devices:
            if device.id == self.gateway_id:
                exists = True

        with io.open(certificate_file) as f:
            certificate = f.read()

        if self.algorithm == "ES256":
            certificate_format = iot_v1.PublicKeyFormat.ES256_PEM
        elif self.algorithm == "RSA":
            certificate_format = iot_v1.PublicKeyFormat.RSA_PEM
        else:
            certificate_format = iot_v1.PublicKeyFormat.RSA_X509_PEM

        device_template = {
            "id": self.gateway_id,
            "credentials": [
                {"public_key": {"format": certificate_format, "key": certificate}}
            ],
            "gateway_config": {
                "gateway_type": iot_v1.GatewayType.GATEWAY,
                "gateway_auth_method": iot_v1.GatewayAuthMethod.ASSOCIATION_ONLY,
            },
        }

        if not exists:
            res = client.create_device(
                request={"parent": parent, "device": device_template}
            )
            logger.info("Created gateway: {}".format(self.gateway_id))
        else:
            logger.info("Gateway '{}' exists, skipping".format(self.gateway_id))

    # service_account_json, project_id, cloud_region, registry_id, device_id
    def _create_device(self, device_id):
        # Check that the device doesn't already exist
        client = iot_v1.DeviceManagerClient()

        exists = False

        parent = client.registry_path(self.project_id, self.cloud_region, self.registry_id)

        devices = list(client.list_devices(request={"parent": parent}))

        for device in devices:
            if device.id == device_id:
                exists = True

        # Create the device
        device_template = {
            "id": device_id,
            "gateway_config": {
                "gateway_type": iot_v1.GatewayType.NON_GATEWAY,
                "gateway_auth_method": iot_v1.GatewayAuthMethod.ASSOCIATION_ONLY,
            },
        }

        if not exists:
            res = client.create_device(
                request={"parent": parent, "device": device_template}
            )
            logger.info("Created device: {}".format(device_id))
        else:
            logger.info("Device '{}' exists, skipping".format(device_id))

    # service_account_json, project_id, cloud_region, registry_id, device_id, gateway_id
    def create_device_and_bind_to_gateway(self, device_id):
        logger.info("Creating device: '{}'".format(device_id))

        client = iot_v1.DeviceManagerClient()

        self._create_device(device_id)

        parent = client.registry_path(self.project_id, self.cloud_region, self.registry_id)

        res = client.bind_device_to_gateway(
            request={"parent": parent, "gateway_id": self.gateway_id, "device_id": device_id}
        )

        logger.info("Device bound: {}".format(device_id))
