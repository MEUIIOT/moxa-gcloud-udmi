import os
import json
import datetime

from google_iot_core_gateway.udmi_handler.modbus_to_dbo import ModbusToDBO


class UDMIHandler:
    def __init__(self, logger, resources_path, udmi_site_model_path):
        self.logger = logger
        self.udmi_site_model_path = udmi_site_model_path
        self.devices = {}

        self._modbus_dbo_map = ModbusToDBO(logger, resources_path).map

    @staticmethod
    def get_timestamp():
        return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    def add_device_to_dict(self, modbus_slave_id, device_id, device_type):
        """
        Method adds new device to dictionary.
        Modbus Slave ID is used as a main dictionary key.
        Dictionary has following structure.

        self.devices = {
            "1": {
                "device_id": "EM-1",
                "device_type": "PM5561",
                "system": {
                    "make_model": "",
                    "firmware": {
                        "version": ""
                    },
                    "serial_no": "",
                    "last_config": "",
                    "operational": ""
                }
                "points": {
                    "phase_voltage_sensor_1": {
                        "present_value": "",
                        "status": {
                            "message": "",
                            "category": "",
                            "timestamp": "",
                            "level": ""
                        }
                    }
                }
            }
        }
        """
        metadata_file_path = os.path.join(self.udmi_site_model_path, "devices", device_id, "metadata.json")
        if not os.path.exists(metadata_file_path):
            self.logger.error(
                f"Device '{device_id}' is not part of UDMI Site Model. Please add this device to the UDMI Site Model and register it to the Google IoT Core with 'registrar' tool")
            return False

        modbus_slave_id = str(modbus_slave_id)

        self.devices[modbus_slave_id] = {}
        self.devices[modbus_slave_id]["device_id"] = device_id
        self.devices[modbus_slave_id]["device_type"] = device_type
        self.devices[modbus_slave_id]["system"] = {
            "make_model": "",
            "firmware": {
                "version": ""
            },
            "serial_no": "",
            "last_config": "",
            "operational": ""
        }

        with open(metadata_file_path, "r") as metadata_file:
            metadata = json.load(metadata_file)

        self.devices[modbus_slave_id]["points"] = metadata["pointset"]["points"]

        for point, point_details in self.devices[modbus_slave_id]["points"].items():
            self.devices[modbus_slave_id]["points"][point]["present_value"] = ""
            self.devices[modbus_slave_id]["points"][point]["status"] = {}
            self.devices[modbus_slave_id]["points"][point]["status"]["message"] = ""
            self.devices[modbus_slave_id]["points"][point]["status"]["category"] = ""
            self.devices[modbus_slave_id]["points"][point]["status"]["timestamp"] = ""
            self.devices[modbus_slave_id]["points"][point]["status"]["level"] = ""

        return True

    def update_device_properties(self, modbus_slave_id, device_type, registry_number, value):
        """
        As the messages are coming in device properties inside the devices dictionary are updated with the latest data.
        Registries '130', '1637', '70' and '50' are system information registries
        Args:
            modbus_slave_id: Modbus Slave ID which is user to identify the device in the dictionary
            device_type: Type of a power meter
            registry_number: registry number that corresponds with DBO name for the point
            value: Value of the registry
        """
        registry_number = str(registry_number)
        modbus_slave_id = str(modbus_slave_id)

        if device_type not in self._modbus_dbo_map:
            self.logger.error(
                f"Modbus-to-DBO map is not defined for the '{device_type}' device type. Please add the '{device_type}.json' file to the 'modbus_dbo_maps' directory")
            return

        if registry_number in self._modbus_dbo_map[device_type]:
            self._update_device_points_present_value(modbus_slave_id, device_type, registry_number, value)
        elif registry_number in self._modbus_dbo_map[device_type]["system"]:
            self._update_system_info(modbus_slave_id, device_type, registry_number, value)

    def _update_system_info(self, modbus_slave_id, device_type, registry_number, value):
        """
        As the messages are coming in device properties inside the devices dictionary are updated with the latest data.
        Args:
            modbus_slave_id: Modbus Slave ID which is user to identify the device in the dictionary
            registry_number: registry number that corresponds with DBO name for the point
            value: Value of the registry
        """
        modbus_slave_id = str(modbus_slave_id)

        point = self._modbus_dbo_map[device_type]["system"][registry_number]["dbo_name"]
        try:
            # TODO: Ask Adam about UDMI system points misalignment with DBO names. And which should be used.
            # Not all DBO names are consistent with UDMI. Possible but?
            # Change it to below?
            # if "version" in point:
            if point == "version":
                self.devices[modbus_slave_id]["system"]["firmware"]["version"] = value
            else:
                self.devices[modbus_slave_id]["system"][point] = value
        except Exception as ex:
            self.logger.debug(f"Exception caught: {ex}")
            self.logger.error(
                f"Error while updating point '{point}' value for the '{self.devices[modbus_slave_id]['device_id']}' device")

    def _update_device_points_present_value(self, modbus_slave_id, device_type, registry_number, value):
        """
        As the messages are coming in device properties inside the devices dictionary are updated with the latest data.
        Args:
            modbus_slave_id: Modbus Slave ID which is user to identify the device in the dictionary
            registry_number: registry number that corresponds with DBO name for the point
            value: Value of the registry
        """
        modbus_slave_id = str(modbus_slave_id)

        point = self._modbus_dbo_map[device_type][registry_number]["dbo_name"]
        try:
            self.devices[modbus_slave_id]["points"][point]["present_value"] = value
            self.devices[modbus_slave_id]["points"][point]["status"]["message"] = "Updated"
            self.devices[modbus_slave_id]["points"][point]["status"]["category"] = ""
            self.devices[modbus_slave_id]["points"][point]["status"]["timestamp"] = self.get_timestamp()
            self.devices[modbus_slave_id]["points"][point]["status"]["level"] = ""
        except Exception as ex:
            self.logger.debug(f"Exception caught: {ex}")
            self.logger.error(
                f"Error while updating point '{point}' value for the '{self.devices[modbus_slave_id]['device_id']}' device")

    def get_event_point_payload(self, modbus_slave_id):
        """
        Converts device dictionary data for particular device into the UDMI payload
        Args:
            modbus_slave_id: Modbus Slave ID which is user to identify the device in the dictionary
        Returns:
            Payload that will be send to event/pointset topic
        """
        modbus_slave_id = str(modbus_slave_id)

        points = {}
        for point, point_details in self.devices[modbus_slave_id]["points"].items():
            points[point] = {}
            points[point]["present_value"] = point_details["present_value"]

        data = {
            "version": 1,
            "timestamp": self.get_timestamp(),
            "points": points
        }
        return json.dumps(data)

    def get_state_payload(self, modbus_slave_id):
        """
        Converts device dictionary data for particular device into the UDMI payload
        Args:
            modbus_slave_id: Modbus Slave ID which is user to identify the device in the dictionary
        Returns:
            Payload that will be send to state topic
        """
        modbus_slave_id = str(modbus_slave_id)

        points = {}
        for point, point_details in self.devices[modbus_slave_id]["points"].items():
            points[point] = {}
            points[point]["status"] = point_details["status"]

        data = {
            "version": 1,
            "timestamp": self.get_timestamp(),
            "system": self.devices[modbus_slave_id]["system"],
            "pointset": {
                "points": points
            }
        }
        return json.dumps(data)

# def json_to_udmi(self):
#     pass

# def create_directory_and_config(self, cloud_region, site_name, registry_id):
#     try:
#         os.makedirs(self.udmi_site_model_path, exist_ok=True)
#     except FileExistsError:
#         pass
#
#     data = {
#         "cloud_region": cloud_region,
#         "site_name": site_name,
#         "registry_id": registry_id
#     }
#
#     cloud_iot_config_file = os.path.join(self.udmi_site_model_path, "cloud_iot_config.json")
#     with open(cloud_iot_config_file, 'w') as cloud_iot_config:
#         json.dump(data, cloud_iot_config)
#
# def create_device_directory(self, device):
#     device_udmi_path = os.path.join(self.udmi_site_model_path, "devices", device)
#
#     try:
#         os.makedirs(device_udmi_path, exist_ok=True)
#     except FileExistsError:
#         pass
#
# def create_gateway_metadata(self, site, gateway_id, devices):
#     metadata_path = os.path.join(self.udmi_site_model_path, "devices", gateway_id, "metadata.json")
#
#     data = {
#         "version": 1,
#         "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
#         "system": {
#             "location": {
#                 "site": site,
#                 "section": ""
#             },
#             "physical_tag": {
#                 "asset": {
#                     "guid": f"guid://{uuid.uuid4().hex}",
#                     "site": site,
#                     "name": gateway_id
#                 }
#             }
#         },
#         "gateway": {
#             "proxy_ids": list(devices.keys())
#         },
#     }
#
#     with open(metadata_path, 'w') as metadata_json:
#         json.dump(data, metadata_json)
