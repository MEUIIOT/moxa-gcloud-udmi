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
├── docs/                     # Documentation files
│   └──                       # Any project relevent document files goes here
├── src/                      # Source code for the project
│   ├── cloud_connector/       # Code for connecting to Google Cloud
│   └── udmi_handler/          # Code for handling UDMI protocols
├── resources/                 # Configuration files
│   └── config-google-gateway.json   # Example configuration file
|   └── modbus_dbo_maps              # Example schneider meter definition files
├── udmi_site_model/              # Configuration files
│   └── cloud_iot_config.json     # Example UDMI project configuration file
|   └── devices               # Example Gateway (Parent) and Devices (Child) UDMI metadata files 
├── LICENSE                   # Project license
├── README.md                 # Project readme (this file)
└── CONTRIBUTING.md           # Guidelines for contributing to the project
