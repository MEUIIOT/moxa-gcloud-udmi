import os
import sys
import json
import datetime
import argparse
import time
from multiprocessing import Queue
from queue import Empty

from google_iot_core_gateway.internal_broker_subscriber.internal_broker_subscriber import MosquittoMQTTSubscriber
from google_iot_core_gateway.gcp_publisher import GoogleIoTCoreMQTTPublisher
from google_iot_core_gateway.udmi_handler.udmi_handler import UDMIHandler
from google_iot_core_gateway.utils.certificates_handler import get_google_root_ca, get_gateway_private_key
from google_iot_core_gateway.utils.config_handler import ConfigHandler
from google_iot_core_gateway.utils.log import setup_logger, update_logger_verbose_level
from google_iot_core_gateway.modbus_gw.modbus_to_json import modbus_to_json

def get_google_cloud_cmd_line_parser():
    """
    Return parser for the Google Cloud command-line args.

    Returns:
        parser - the constructed parser, for use by main cmdline parser
    """
    parser = argparse.ArgumentParser(add_help=False)

    group = parser.add_argument_group('Cloud settings')

    group.add_argument("-google-cloud-config-file", dest="google_cloud_config_file", metavar="CONFIG_FILE",
                       help="Google Cloud Configuration file. If not provided explicitly default config.json will be used")

    group.add_argument("-google-cloud-region", dest="google_cloud__cloud_region", type=str, metavar="REGION",
                       choices=['europe-west1', 'us-central1', 'asia-east1'],
                       help="Overwrite Google Cloud Region")
    group.add_argument("-google-cloud-project-id", dest="google_cloud__project_id", type=str, metavar="PROJECT_ID",
                       help="Overwrite Google Cloud Project ID")
    group.add_argument("-google-cloud-hostname", dest="google_cloud__mqtt_bridge_hostname", type=str,
                       metavar="HOSTNAME", help="Overwrite Google Cloud Hostname")
    group.add_argument("-google-cloud-port", dest="google_cloud__mqtt_bridge_port", type=str, metavar="PORT",
                       help="Overwrite Google Cloud Port")

    group = parser.add_argument_group('Site Details settings')
    group.add_argument("-site-details-name", dest="site_details__name", type=str, metavar="NAME",
                       help="Overwrite Site Registry Name")
    group.add_argument("-site-details-registry-id", dest="site_details__registry_id", type=str, metavar="REGISTRY_ID",
                       help="Overwrite Site Registry ID")
    group.add_argument("-site-details-gateway-id", dest="site_details__gateway_id", type=str, metavar="GATEWAY_ID",
                       help="Overwrite Google Cloud Gateway ID")

    group = parser.add_argument_group('Environment settings')
    group.add_argument("-udmi-site-model-path", dest="udmi_site_model_path", type=str, metavar="PATH",
                       help="Overwrite UDMI Site Model path")
    group.add_argument("-resources-path", dest="resources_path", type=str, metavar="PATH",
                       help="Overwrite resources path")

    return parser


def parse_command_line_args(args=None, parents=None):
    """
    This function is invoked only when module is run as a standalone application

    Parse and execute the call from command-line.
    Args:
        args: List of strings to parse.
        parents: list pf parent parsers to include. Note: these are used only to construct
            a proper help message and must be parsed separately.
    Returns:
        The parsed arguments as Namespace
    """
    parser = argparse.ArgumentParser(allow_abbrev=False, add_help=True, parents=parents)

    parser.add_argument("-internal-broker-hostname", dest="internal_broker__mqtt_bridge_hostname", type=str,
                        metavar="HOSTNAME", help="Overwrite Internal Broker Hostname")
    parser.add_argument("-internal-broker-port", dest="internal_broker__mqtt_bridge_port", type=int,
                        metavar="PORT", help="Overwrite Internal Broker Port")
    parser.add_argument("-v", "--verbose", dest="verbose_level", default=None, help="Turn on console DEBUG mode [-v 2]")

    parsed_args, unknown_args = parser.parse_known_args(args)
    return parsed_args


def _get_google_iot_core_publisher(logger, config):
    """
        Set up Google IoT Core publisher client.
        Args:
            logger: logger
            config: Configuration
        Returns:
            Google IoT Core Publisher
        """
    private_key_file_path, encryption_algorithm = get_gateway_private_key(logger, config.udmi_site_model_path,
                                                                          config.site_details__gateway_id)
    ca_cert = get_google_root_ca(config.resources_path)

    google_iot_core_publisher = GoogleIoTCoreMQTTPublisher(logger, config.site_details__devices,
                                                           cloud_region=config.google_cloud__cloud_region,
                                                           project_id=config.google_cloud__project_id,
                                                           registry_id=config.site_details__registry_id,
                                                           gateway_id=config.site_details__gateway_id,
                                                           mqtt_bridge_hostname=config.google_cloud__mqtt_bridge_hostname,
                                                           mqtt_bridge_port=config.google_cloud__mqtt_bridge_port,
                                                           private_key_file=private_key_file_path,
                                                           ca_cert=ca_cert,
                                                           jwt_signing_algorithm=encryption_algorithm)

    return google_iot_core_publisher


def _get_udmi_handler(logger, config):
    """
        Set up UDMI handler.
        Args:
            logger: logger
            config: Configuration
        Returns:
            UDMI handler
        """
    udmi_handler = UDMIHandler(logger, config.resources_path, config.udmi_site_model_path)

    for device_id in list(config.site_details__devices.keys()):
        modbus_slave_id = config.site_details__devices[device_id]["modbus_slave_id"]
        device_type = config.site_details__devices[device_id]["type"]
        device_added = udmi_handler.add_device_to_dict(modbus_slave_id, device_id, device_type)
        if not device_added:
            del config.site_details__devices[device_id]

    return udmi_handler


def prepare_google_cloud_environment(logger, config):
    """
    Set up Google IoT Core publisher client and UDMI handler.
    Args:
        logger: logger
        config:
    Returns:
        Namespace list of args
    """
    udmi_handler = _get_udmi_handler(logger, config)
    google_iot_core_publisher = _get_google_iot_core_publisher(logger, config)

    return google_iot_core_publisher, udmi_handler


def process_payloads(logger, google_iot_core_queue, udmi_handler):
    """
    Method will process received messages and update device properties

    Sample payload:
    {'slave_id': 2, 'fc': 3, 'data': {128: 54, 129: 920, 130: 4565}, 'error': None}

    Args:
        logger: logger
        google_iot_core_queue: Messages queue
        udmi_handler: object with devices dictionary
    Returns:
        True if connected, False otherwise
    """
    try:
        payload = google_iot_core_queue.get_nowait()
        payload = json.loads(payload)
        
        rtu_request = bytes.fromhex(payload['rtu_request'])
        rtu_response = bytes.fromhex(payload['rtu_response'])
       
        logger.debug("*************************************** build modbus to JSON ******************************")
        logger.info("Modbus To JSON Started!")        
        payload = modbus_to_json(rtu_request, rtu_response)
        logger.debug("*************************************** build modbus to JSON ******************************")
  
    except Empty:
        return
    except Exception as ex:
        logger.error(f"Caught an Exception when getting queue item. Exception: {ex}")
        return
    
    if payload:
        payload = json.loads(payload)
        modbus_slave_id = str(payload["slave_id"])

        if modbus_slave_id not in udmi_handler.devices:
            logger.debug(
                f"Modbus device '{modbus_slave_id}' is not configured to send it's telemetry to the could. Please add this device to the 'config-google-gateway.json' file and UDMI Site Model if you want to report it's state")
            return

        error = payload["error"]
        if error is not None:
            udmi_handler.devices[modbus_slave_id]["system"]["operational"] = False
        else:
            udmi_handler.devices[modbus_slave_id]["system"]["operational"] = True

            device_type = udmi_handler.devices[modbus_slave_id]["device_type"]

            function_code = payload["fc"]
            data = payload["data"]

            if function_code == 3 or function_code == 4:
                try:
                    for registry, value in data.items():
                        udmi_handler.update_device_properties(modbus_slave_id, device_type, registry, value)
                except (ValueError, AttributeError):
                    logger.error(
                        f"Data format in received payload is not correct! Expected format is key-value pairs. Received data: '{data}'")
            
def publish_payloads(logger, google_iot_core_publisher, udmi_handler, sample_rate_set):
    """
    Publish payloads to the Google IoT Core topics
    Args:
        logger: Logger
        google_iot_core_publisher: Google IoT Core client
        udmi_handler: Gets the devices current state
        sample_rate_set: Time in seconds to the next payload publishing
    Returns:
        Time of next payload publishing
    """
    for device, device_details in udmi_handler.devices.items():
        logger.info(f"Publishing payload for device '{device_details['device_id']}' on topic 'state'")
        payload = udmi_handler.get_state_payload(device)
        
        logger.debug(f"State payload: {payload}")
        google_iot_core_publisher.publish(device_details["device_id"], payload)

        logger.info(f"Publishing payload for device '{device_details['device_id']}' on topic 'events/pointset'")
        payload = udmi_handler.get_event_point_payload(device)
        
        logger.debug(f"Pointset payload: {payload}")
        google_iot_core_publisher.publish(device_details["device_id"], payload, topic="events/pointset")

    logger.info("Payloads published")

    next_payload_publish_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=sample_rate_set)
    return next_payload_publish_time


def start_google_iot_core_gateway(logger, args, root_dir=None):
    """
        Main function responsible for setting up environment, parsing configs, establishing connections
        to Internal Broker and Google IoT Core, and processing messages.
        Args:
            args: List of strings to parse. The default is taken from sys.argv.
            logger: Logger
            root_dir:
        """
    config = ConfigHandler(logger, args, root_dir)
    #update_logger_verbose_level(logger, config.verbose_level)
    
    max_queue_size = 50    
    google_iot_core_queue = Queue(maxsize=max_queue_size)
    int_broker_subscriber = MosquittoMQTTSubscriber(logger, google_iot_core_queue,
                                                    config.internal_broker__mqtt_bridge_hostname,
                                                    config.internal_broker__mqtt_bridge_port,
                                                    config.internal_broker__trusted_root_ca,
                                                    config.internal_broker__x509_certificate,
                                                    config.internal_broker__private_key,
                                                    config.internal_broker__tls_insecure_set,
                                                    config.internal_broker__enable_tls
                                                    )
    int_broker_subscriber.run()

    google_iot_core_publisher, udmi_handler = prepare_google_cloud_environment(logger, config)

    # Loop variables setup
    sample_rate_set = config.google_cloud__sample_rate_set
    next_payload_publish_time = datetime.datetime.utcnow()

    # Main loop start
    while True:
        time.sleep(1)

        process_payloads(logger, google_iot_core_queue, udmi_handler)

        is_connected = google_iot_core_publisher.is_connection_open()
        if not is_connected:
            continue

        if next_payload_publish_time < datetime.datetime.utcnow():
            next_payload_publish_time = publish_payloads(logger, google_iot_core_publisher, udmi_handler,
                                                         sample_rate_set)


def start_standalone_google_iot_core_gateway(assigned_args=None, logger=None):
    """
    This function is invoked only when module is run as a standalone application

    Main function responsible for parsing arguments and setting up logger
    Args:
        assigned_args: List of strings to parse. The default is taken from sys.argv.
        logger: Logger
    """
    args = parse_command_line_args(args=assigned_args, parents=[get_google_cloud_cmd_line_parser()])

    if not logger:
        logger = setup_logger()

    start_google_iot_core_gateway(logger, args)
