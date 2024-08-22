# Moxa GCloud UDMI Integration

[![License](https://img.shields.io/github/license/MEUIIOT/moxa-gcloud-udmi)](LICENSE)
[![GitHub issues](https://img.shields.io/github/issues/MEUIIOT/moxa-gcloud-udmi)](https://github.com/MEUIIOT/moxa-gcloud-udmi/issues)
[![GitHub forks](https://img.shields.io/github/forks/MEUIIOT/moxa-gcloud-udmi)](https://github.com/MEUIIOT/moxa-gcloud-udmi/network)

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)

## Overview
The **Moxa GCloud UDMI Integration** project provides an interface between Moxa's edge computing devices for example UC-8200 with Google IoT Core/ClearBlade through the **UDMI (Unified Device Management Interface)** framework. This integration enables modbus telemetry reporting for industrial IoT applications according to UDMI specification.
![image](https://github.com/user-attachments/assets/0a59dbb3-8941-408a-9212-7d70b7078d9e)

## Features
- **Cloud Integration:** Connect Moxa devices to Google Cloud IoT Core/ClearBlade via UDMI and MQTT.
- **Telemetry Reporting:** Send real-time modbus telemetry data according to UDMI pointset and state payload from edge devices to the cloud
- **Modbus to JSON Decoder:** Decode raw modbus rtu request and response as per Schneider meter definition files

## Project Structure
```plaintext
moxa-gcloud-udmi/
│
├── docs/                                 # Documentation files
│   └──                                   # Any project relevent document files goes here
├── src/                                  # Source code for the project
|   └── main.py                           # Main entry file 
│   ├── google_iot_core_gateway/          # Google IoT Core/ClearBlade module
│       └── internal_broker_subscriber/   # Code for subscribing raw rtu request and response from internal mosquitto broker
│       └── modbus_gw/                    # Code for decoding raw rtu request/response as per Schneider meter definition file
│       └── udmi_handler/                 # Code for udmi mapping for modbus to dbo names and constructing payload pointset and state
│       └── utils/                        # Code for Google IoT Core authentication and Configuration handlers
│       └── gcp_manager.py                # Code for create registry, devices and gateway on the Google Iot Core.
│       └── gcp_publisher.py              # Code for connecting and publishing telemetry to the Google Iot Core using paho mqtt library
│       └── gcp_handler.py                # Code for starting the google IoT Core function and other initialization task. This file is called in main.py 
├── resources/                            # Resource dir for configuration
│   └── config-google-gateway.json        # Example configuration file google clear blade IoT core
|   └── modbus_dbo_maps                   # Example schneider meter definition files e.g PM5111
├── udmi_site_model/                      # Resource dir for UDMI site models 
│   └── cloud_iot_config.json             # Example UDMI project configuration file
|   └── devices                           # Example meta data files Gateway CGW-1 and Devices EM-1, EM-2 
├── LICENSE                               # Project license
├── README.md                             # Project readme (this file)
└── CONTRIBUTING.md                       # Guidelines for contributing to the project
```

## Installation
To set up the project locally, follow these steps:
### Preconditions
1. Python version 3.9 - abel to run with `python3.9` command
2. Git
3. pyinstaller
4. pip

### Clone the repository:
```bash
sudo git clone https://github.com/MEUIIOT/moxa-gcloud-udmi.git
cd moxa-gcloud-udmi
```
### Install required `pip` packages
```bash
sudo pip3.9 install -r src/google_iot_core_gateway/requirements.txt
```
