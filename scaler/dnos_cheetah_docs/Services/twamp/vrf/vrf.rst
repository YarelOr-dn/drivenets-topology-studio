services twamp vrf
------------------

**Minimum user role:** operator

To configure a TWAMP server per VRF:

**Command syntax: vrf [vrf-name]**

**Command mode:** config

**Hierarchies**

- services twamp

**Note**

- Only in-band VRFs are supported

**Parameter table**

+-----------+----------------------+------------------+---------+
| Parameter | Description          | Range            | Default |
+===========+======================+==================+=========+
| vrf-name  | The name of the VRF. | | string         | \-      |
|           |                      | | length 1-255   |         |
+-----------+----------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# twamp
    dnRouter(cfg-srv-twamp)# vrf default
    dnRouter(cfg-srv-twamp-vrf)#

    dnRouter(cfg-srv)# twamp vrf my_vrf
    dnRouter(cfg-srv-twamp-vrf)#


**Removing Configuration**

To delete the configuration under a specific VRF:
::

    dnRouter(cfg-srv-twamp)# no vrf my_vrf

To delete the configuration for all VRFs:
::

    dnRouter(cfg-srv-twamp)# no vrf

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
