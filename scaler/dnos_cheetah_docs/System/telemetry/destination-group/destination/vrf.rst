system telemetry destination-group destination port vrf
-------------------------------------------------------

**Minimum user role:** operator

To configure a VRF for use to the telemetry destination:

**Command syntax: vrf [vrf]**

**Command mode:** config

**Hierarchies**

- system telemetry destination-group destination port

**Parameter table**

+-----------+------------------------------------+------------------+---------+
| Parameter | Description                        | Range            | Default |
+===========+====================================+==================+=========+
| vrf       | VRF to use for destination session | | string         | default |
|           |                                    | | length 1-255   |         |
+-----------+------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# telemetry
    dnRouter(cfg-system-telemetry)# destination-group lab
    dnRouter(cfg-system-telemetry-dest-group)# destination ip 1.1.1.1 port 34000
    dnRouter(cfg-system-telemetry-dest-group-dest)# vrf default


**Removing Configuration**

To revert vrf to default:
::

    dnRouter(cfg-system-telemetry-dest-group-dest)# no vrf

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
