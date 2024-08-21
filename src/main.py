#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This software is licensed under GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007

"""This is the main script of Modbus JSON to UDMI Google Cloud IoT Core/ClearBlade"""

import argparse
import asyncio
import queue
import threading

from app_data import app_data
from google_iot_core_gateway.gcp_handler import start_google_iot_core_gateway, get_google_cloud_cmd_line_parser, start_standalone_google_iot_core_gateway
from google_iot_core_gateway import __version__ as version, ROOT_DIR
from google_iot_core_gateway.utils.config_handler import ConfigHandler
from google_iot_core_gateway.utils.log import setup_logger, update_logger_verbose_level


logger = setup_logger()

def get_internal_broker_cmd_line_parser() -> argparse.ArgumentParser:
    """Return parser for the Internal Broker command-line args.

    Returns:
        parser - the constructed parser, for use by main cmdline parser
    """
    parser = argparse.ArgumentParser(add_help=False)

    group = parser.add_argument_group('Internal Broker settings')
    group.add_argument("-internal-broker-hostname", dest="internal_broker__mqtt_bridge_hostname", type=str,
                       metavar="HOSTNAME",
                       help="Overwrite Internal Broker Hostname. Default ['127.0.0.1']")
    group.add_argument("-internal-broker-port", dest="internal_broker__mqtt_bridge_port", type=int,
                       metavar="PORT",
                       help="Overwrite Internal Broker Port. Default[1883]")
    return parser

def parse_main_cmd_line_args(args: list[str] = None,
                             parents: list[argparse.ArgumentParser] = []) -> argparse.Namespace:
    """Parse the main command-line args.

    Args:
        args: List of strings to parse.
        parents: list pf parent parsers to include. Note: these are used only to construct
            a proper help message and must be parsed separately.

    Returns:
        The parsed arguments as Namespace
    """
    # parser = argparse.ArgumentParser(prog="appcmd", description=globals()['__doc__'], epilog="!!Note: .....")
    parser = argparse.ArgumentParser(allow_abbrev=False, add_help=True, parents=parents)

    parser.add_argument("-c", dest="config_file",
                        help="Configuration file to use. If not provided explicitly default %(default)s will be used")

    # parser.add_argument("-l", dest="file_level", metavar="File logging", type=int, action="store", default=None, help="Turn on file logging with level.")
    parser.add_argument("-v", "--verbose", dest="verbose_level", default=None, help="Turn on console DEBUG mode [-v 2]")
    parser.add_argument("-V", "--version", action="version", version=version)

    parsed_args = parser.parse_args(args)

    return parsed_args


if __name__ == "__main__":

    # parse the main command line parameters
    args = parse_main_cmd_line_args(parents=[
                                         get_google_cloud_cmd_line_parser(),
                                         get_internal_broker_cmd_line_parser()])
  
    thread_google_bos_gateway = threading.Thread(
        target=start_google_iot_core_gateway,
        args=(logger, args, ROOT_DIR),
        daemon=False
    )
      
    try:
        thread_google_bos_gateway.start()
        logger.info("MQTT Google IoT Core Gateway Thread Started!")
        
        timeout = 1.0
       
    except (SystemExit, KeyboardInterrupt) as e:
        if isinstance(e, KeyboardInterrupt):
            print('Keyboard Interrupted')

        # Clean up the connection
        logger.warning(f"MQTT Google IoT Core Gateway Thread: waiting to join! ({timeout=})")
        thread_google_bos_gateway.join(timeout=timeout)
       
    finally:
        #loop.close()
        pass
      
         