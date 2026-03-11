network-services vrf instance in-band-management
------------------------------------------------

**Minimum user role:** operator

To enter the in-band management configuration level:

**Command syntax: in-band-management**

**Command mode:** config

**Hierarchies**

- network-services vrf instance

**Note**
The no command deletes the in-band-management configuration only if the configuration isn't used by management protocols.

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# vrf instance my_vrf
    dnRouter(cfg-netsrv-vrf)# in-band-management
    dnRouter(cfg-vrf-inband-mgmt)#

    dnRouter(cfg-netsrv-vrf)# no in-band-management


**Removing Configuration**

To remove services for non-default VRFs:
::

    no in-band-management

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
