network-services vrf instance
-----------------------------

**Minimum user role:** operator

To configure a VRF instance:

**Command syntax: instance [vrf-name]**

**Command mode:** config

**Hierarchies**

- network-services vrf

**Note**

- The legal string length is 1..255 characters.

- Illegal characters include any whitespace, non-ascii, and the following special characters (separated by commas): #,!,',”,\

- 'no' command deletes the vrf instance and the protocols hierarchy dependencies under the VRF instance. Management protocols, services and other dependencies that rely on the VRF instance or its associated interfaces must be deleted explicitly before deleting the VRF instance.

**Parameter table**

+-----------+------------------------------------------------+------------------+---------+
| Parameter | Description                                    | Range            | Default |
+===========+================================================+==================+=========+
| vrf-name  | The name of the vrf -- used to address the vrf | | string         | \-      |
|           |                                                | | length 1-255   |         |
+-----------+------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# vrf instance customer_vrf_1
    dnRouter(cfg-netsrv-vrf-inst)#


**Removing Configuration**

To remove the specified VRF instance:
::

    dnRouter(cfg-netsrv-vrf)# no instance customer_vrf_1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
