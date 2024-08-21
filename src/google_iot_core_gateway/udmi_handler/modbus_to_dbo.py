import os
import json
import logging
from pathlib import Path


class ModbusToDBO:
    def __init__(self, logger, resources_path):
        self.logger = logger
        self.map = {}

        self._populate_the_map(resources_path)

    def _populate_the_map(self, resources_path):
        self.logger.debug(f"Populating the Modbus-To-DBO map")
        modbus_dbo_maps_path = os.path.join(resources_path, "modbus_dbo_maps")
        modbus_dbo_maps_path = Path(modbus_dbo_maps_path)
        json_files_in_modbus_dbo_maps_path = (entry for entry in modbus_dbo_maps_path.iterdir() if
                                              entry.is_file() and ".json" in entry.name)

        for item in json_files_in_modbus_dbo_maps_path:
            self.logger.info(f"Processing Modbus-To-DBO map: {item.name}")
            pm_type = item.name.replace(".json", "")
            with item.open() as json_file:
                data = json.load(json_file)
                self.map[pm_type] = data
        self.logger.debug(f"Populating the Modbus-To-DBO map completed!")


if __name__ == "__main__":
    logger = logging.getLogger()
    resource_path = "/tmp/pycharm_project_309/resources"
    map = ModbusToDBO(logger, resource_path).map
    print(map["PM5561"])
