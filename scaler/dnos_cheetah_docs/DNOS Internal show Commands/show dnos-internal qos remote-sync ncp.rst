show dnos-internal remote-sync qos ncp
--------------------------------------

**Minimum user role:** viewer

Display remote ncp QoS running/candidate config to be applied locally:

**Command syntax: show dnos-internal remote-sync qos ncp [ncp-id]** running candidate

**Command mode:** operation

**Parameter table**

The displayed parameters are:

+----------------+------------------------------------------------------------------+------------------------+
| Parameter      | Description                                                      | Values                 |
+----------------+------------------------------------------------------------------+------------------------+
| running        | Display QoS config of remote NCP currently applied on this NCP   | running config(json)   |
|                |                                                                  |                        |
|                |                                                                  |                        |
|                |                                                                  |                        |
+----------------+------------------------------------------------------------------+------------------------+
| candidate      | Display last received QoS config of remote ncp                   | candidate config(json) |
|                |                                                                  |                        |
+----------------+------------------------------------------------------------------+------------------------+

**Example**
::

    dnRouter# show dnos-internal remote-sync qos ncp 3

    Remote running for ncp-id 3:

    {}

    Remote candidate for ncp-id 3

    {
      "drivenets_top": {
        "qos": {
          "traffic_class_maps": {
            "traffic_class_map": {
              "QOS-TAG-1": {
                "config_items": {
                  "qos_tag": [
                    1
                  ]
                }
              },
              "QOS-TAG-2": {
                "config_items": {
                  "qos_tag": [
                    2
                  ]
                }
              }
            }
          },
          "policies": {
            "policy": {
              "GENERIC_EGRESS_QOS_POLICY": {
                "rules": {
                  "rule": {
                    "10": {
                      "actions": {
                        "action": {
                          "queue": {
                            "queue": {
                              "config_items": {
                                "af": {
                                  "bandwidth_percent": 10,
                                  "queue_size_microseconds": 640
                                }
                              }
                            }
                          }
                        }
                      },
                      "config_items": {
                        "rule_id": 10,
                        "traffic_class_map": "QOS-TAG-1"
                      }
                    },
                    "default": {
                      "actions": {
                        "action": {
                          "queue": {
                            "queue": {
                              "config_items": {
                                "df": {
                                  "bandwidth_percent": 10,
                                  "queue_size_microseconds": 640
                                }
                              }
                            }
                          }
                        }
                      },
                      "config_items": {
                        "rule_id": "default"
                      }
                    }
                  }
                }
              }
            }
          }
        },
        "interfaces": {
          "interface": {
            "ge200-3/0/0/0": {
              "breakout": {
                "config_items": {
                  "state": "child"
                }
              },
              "qos_target": {
                "qos_target_entry": {
                  "out GENERIC_EGRESS_QOS_POLICY": {
                    "config_items": {
                      "policy_name": "GENERIC_EGRESS_QOS_POLICY"
                    }
                  }
                }
              }
            },
            "ge200-3/0/0/1": {
              "breakout": {
                "config_items": {
                  "state": "child"
                }
              },
              "qos_target": {
                "qos_target_entry": {
                  "out GENERIC_EGRESS_QOS_POLICY": {
                    "config_items": {
                      "policy_name": "GENERIC_EGRESS_QOS_POLICY"
                    }
                  }
                }
              }
            },
            "ge400-3/0/0": {
              "breakout": {
                "config_items": {
                  "state": "parent"
                }
              }
            }
          }
        }
      }
    }

.. **Help line:** Display information about qos sync for specific remote ncp

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 19.10       | Command introduced    |
+-------------+-----------------------+
