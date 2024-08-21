# For gateway e.g CGW-1 modify the following properties according to your cloud enviornment
  and child devices connected to it

  Note: guid must be different for gateway as well as devices 
        which can be created from command line tool


{
  "system": {
    "location": {
      "site": "KGX-1",
    },
    "physical_tag": {
      "asset": {
        "guid": "guid://a8159395-2d69-4480-8252-8b678f6813da",
        "site": "KGX-1",
        "name": "CGW-1"
      }
    }
  },
  "gateway": {
    "proxy_ids": [ "EM-1", "EM-2" ]


# For devices e.g EM-1 modify the following properties according to your cloud enviornment

  "system": {
    "location": {
      "site": "KGX-1",
    },
    "physical_tag": {
      "asset": {
        "guid": "guid//0757e4fc-dc8f-4cbe-9471-19336531f608",
        "site": "KGX-1",
        "name": "EM-E"
      }
    }
  },
  "gateway": {
    "gateway_id": "CGW-1"
  }

