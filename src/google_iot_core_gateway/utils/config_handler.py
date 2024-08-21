#!/usr/bin/env python3.9
import os
import sys
import json

from google_iot_core_gateway.utils.log import update_logger_verbose_level


class ConfigHandler:

    def __init__(self, logger, args=None, root_dir=None):
        self.logger = logger

        # Default configuration will be loaded if not specified in config file
        self.internal_broker__mqtt_bridge_hostname = "127.0.0.1"
        self.internal_broker__mqtt_bridge_port = 8883
        self.internal_broker__trusted_root_ca = None
        self.internal_broker__x509_certificate =  None
        self.internal_broker__private_key = None
        self.internal_broker__tls_insecure_set = False
        self.internal_broker__enable_tls = False

        self.google_cloud__cloud_region = "europe-west1"
        self.google_cloud__project_id = "moxa01-iot-core"
        self.google_cloud__sample_rate_set = 1800
        self.google_cloud__mqtt_bridge_hostname = "mqtt.googleapis.com"
        self.google_cloud__mqtt_bridge_port = 443

        self.site_details__name = "KGX-1"
        self.site_details__registry_id = "KGX-1"
        self.site_details__gateway_id = "CGW-1"
        self.site_details__devices = {
            "EM-1": {
                "id": "",
                "type": "simulator",
                "modbus_slave_id": 1
            }
        }
       
        #self.verbose_level = None
       
        self.udmi_site_model_path = "/home/moxa/udmi_site_model"
        #self.resources_path = os.path.join("/home/moxa/modbus_parsing/moxa-uc8200-ei-google-project", "resources")
        self.resources_path = os.path.join(root_dir, "resources")
        if not os.path.isdir(self.resources_path):
            self.resources_path = root_dir

        self._google_cloud_config_file = os.path.join(self.resources_path, 'config-google-gateway.json')
        if args:
            if args.verbose_level is not None:
                update_logger_verbose_level(logger, args.verbose_level)
            if args.google_cloud_config_file is not None:
                self._google_cloud_config_file = args.google_cloud_config_file

        self._parse_module_configuration()
        self._parse_args_configuration(args)
        self._parse_udmi_site_model_configuration()
        self._print_configuration()

    def _read_ext_config(self, config_file=None):
        """
        Read configuration file
        """
        if config_file is None:
            config_file = self._google_cloud_config_file
        try:
            self.logger.info("*********** Reading External Config: {} ***********".format(config_file))
            with open(config_file) as json_data_file:
                cfg_obj = json.load(json_data_file)
                self.logger.debug("  ******* External Config:\n  {} *******".format(cfg_obj))
                return cfg_obj
        except (FileNotFoundError, IOError) as e:
            self.logger.error(f"Invalid path to the config file: {config_file}")
            self.logger.error(e)
            return None

    # Parse udmi_site_model file
    def _parse_udmi_site_model_configuration(self):
        """
        Reads the UDMI Site Model directory config file for the Google Iot Core connection.
        """
        self.logger.info("*********** Parse UDMI Site Model Configuration ***********")
        udmi_site_model_config = os.path.join(self.udmi_site_model_path, "cloud_iot_config.json")
        ext_conf = self._read_ext_config(config_file=udmi_site_model_config)

        if not ext_conf:
            self.logger.error("*********** Empty UDMI Site Model Configuration! ***********")
            sys.exit(1)
        else:
            if ext_conf["cloud_region"]:
                self.google_cloud__cloud_region = ext_conf["cloud_region"]
            if ext_conf["site_name"]:
                self.site_details__name = ext_conf["site_name"]
            if ext_conf["registry_id"]:
                self.site_details__registry_id = ext_conf["registry_id"]

    # Parse config.json file
    def _parse_module_configuration(self):
        """
        Reads the Module config file for the Modbus Slaves ID, and also Internal Broker and Google Iot Core connection.
        """
        self.logger.info("*********** Parse Module Configuration ***********")
        ext_conf = self._read_ext_config()

        if not ext_conf:
            self.logger.error("*********** Empty Module Configuration! ***********")
            sys.exit(1)
        else:
            if ext_conf["internal_broker"]["mqtt_bridge_hostname"]:
                self.internal_broker__mqtt_bridge_hostname = ext_conf["internal_broker"]["mqtt_bridge_hostname"]
            if ext_conf["internal_broker"]["mqtt_bridge_port"]:
                self.internal_broker__mqtt_bridge_port = ext_conf["internal_broker"]["mqtt_bridge_port"]
            if ext_conf["internal_broker"]["trusted_root_ca"]:
                self.internal_broker__trusted_root_ca = ext_conf["internal_broker"]["trusted_root_ca"]
            if ext_conf["internal_broker"]["x509_certificate"]:
                self.internal_broker__x509_certificate = ext_conf["internal_broker"]["x509_certificate"]
            if ext_conf["internal_broker"]["private_key"]:
                self.internal_broker__private_key = ext_conf["internal_broker"]["private_key"]
            try:
               if ext_conf["internal_broker"]["tls_insecure_set"]:
                  self.internal_broker__tls_insecure_set = ext_conf["internal_broker"]["tls_insecure_set"]
                  self.logger.info("  internal_broker__tls_insecure_set: {}".format(self.internal_broker__tls_insecure_set))
            except:
                   pass

            if ext_conf["internal_broker"]["enable_tls"]:
                self.internal_broker__enable_tls = ext_conf["internal_broker"]["enable_tls"]

            if ext_conf["google_cloud"]["project_id"]:
                self.google_cloud__project_id = ext_conf["google_cloud"]["project_id"]
            if ext_conf["google_cloud"]["sample_rate_set"]:
                self.google_cloud__sample_rate_set = ext_conf["google_cloud"]["sample_rate_set"]
            if ext_conf["google_cloud"]["mqtt_bridge_hostname"]:
                self.google_cloud__mqtt_bridge_hostname = ext_conf["google_cloud"]["mqtt_bridge_hostname"]
            if ext_conf["google_cloud"]["mqtt_bridge_port"]:
                self.google_cloud__mqtt_bridge_port = ext_conf["google_cloud"]["mqtt_bridge_port"]

            if ext_conf["site_details"]["gateway_id"]:
                self.site_details__gateway_id = ext_conf["site_details"]["gateway_id"]
            if ext_conf["site_details"]["proxy_ids"]:
                self.site_details__devices = ext_conf["site_details"]["proxy_ids"]

            if ext_conf["environment_setup"]["udmi_site_model_path"]:
                self.udmi_site_model_path = ext_conf["environment_setup"]["udmi_site_model_path"]

    # Parse args
    def _parse_args_configuration(self, args=None):
        """
        Read command line arguments and overrides the setting provided in the config files
        """
        self.logger.info("*********** Parse args Configuration ***********")
        if not args:
            self.logger.info("*********** Empty args Configuration! Skipping! ***********")
            return
        else:
            if args.internal_broker__mqtt_bridge_hostname is not None:
                self.internal_broker__mqtt_bridge_hostname = args.internal_broker__mqtt_bridge_hostname
            if args.internal_broker__mqtt_bridge_port is not None:
                self.internal_broker__mqtt_bridge_port = args.internal_broker__mqtt_bridge_port

            if args.google_cloud__cloud_region is not None:
                self.google_cloud__cloud_region = args.google_cloud__cloud_region
            if args.google_cloud__project_id is not None:
                self.google_cloud__project_id = args.google_cloud__project_id
            if args.google_cloud__mqtt_bridge_hostname is not None:
                self.google_cloud__mqtt_bridge_hostname = args.google_cloud__mqtt_bridge_hostname
            if args.google_cloud__mqtt_bridge_port is not None:
                self.google_cloud__mqtt_bridge_port = args.google_cloud__mqtt_bridge_port

            if args.site_details__name is not None:
                self.site_details__name = args.site_details__name
            if args.site_details__registry_id is not None:
                self.site_details__registry_id = args.site_details__registry_id
            if args.site_details__gateway_id is not None:
                self.site_details__gateway_id = args.site_details__gateway_id

            if args.udmi_site_model_path is not None:
                self.udmi_site_model_path = args.udmi_site_model_path

    def _print_configuration(self):
        self.logger.info(
            "  internal_broker__mqtt_bridge_hostname: {}".format(self.internal_broker__mqtt_bridge_hostname))
        self.logger.info("  internal_broker__mqtt_bridge_port: {}".format(self.internal_broker__mqtt_bridge_port))
        self.logger.info("  internal_broker__trusted_root_ca: {}".format(self.internal_broker__trusted_root_ca))
        self.logger.info("  internal_broker__x509_certificate: {}".format(self.internal_broker__x509_certificate))
        self.logger.info("  internal_broker__private_key: {}".format(self.internal_broker__private_key))
        self.logger.info("  internal_broker__enable_tls: {}".format(self.internal_broker__enable_tls))

        self.logger.info("  google_cloud__cloud_region: {}".format(self.google_cloud__cloud_region))
        self.logger.info("  google_cloud__project_id: {}".format(self.google_cloud__project_id))
        self.logger.info(
            "  google_cloud__mqtt_bridge_hostname: {}".format(self.google_cloud__mqtt_bridge_hostname))
        self.logger.info("  google_cloud__mqtt_bridge_port: {}".format(self.google_cloud__mqtt_bridge_port))

        self.logger.info("  site_details__name: {}".format(self.site_details__name))
        self.logger.info("  site_details__registry_id: {}".format(self.site_details__registry_id))
        self.logger.info("  site_details__gateway_id: {}".format(self.site_details__gateway_id))
        self.logger.info("  site_details__devices: {}".format(self.site_details__devices))

        self.logger.info("  udmi_site_model_path: {}".format(self.udmi_site_model_path))
        self.logger.info("  resources_path: {}".format(self.resources_path))

        self.logger.info("*********** Parse Configuration Successful! ***********")
