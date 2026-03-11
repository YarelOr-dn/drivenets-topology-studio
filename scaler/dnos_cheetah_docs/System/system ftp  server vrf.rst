system ftp server vrf
---------------------

**Minimum user role:** operator

To set FTP client-list attachment per VRF:

**Command syntax: server vrf [vrf-name]**

**Command mode:** config

**Hierarchies**

- system ftp


**Note**

- Notice the change in prompt

.. - vrf definition level is introduced for attaching client-list.

	- vrf "default" represents the in-band management, while vrf "mgmt0" represents the out-of-band management.

	- no command deletes the configuration under the specific vrf.

**Parameter table**

+-----------+------------------------------------------------------------------------------+---------------------+---------+
| Parameter | Description                                                                  | Range               | Default |
+===========+==============================================================================+=====================+=========+
| vrf-name  | Allows to define separate FTP client-lists per VRF (in-band and out-of-band) | default - in-band   | \-      |
|           |                                                                              | mgmt0 - out-of-band |         |
+-----------+------------------------------------------------------------------------------+---------------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# ftp
	dnRouter(cfg-system-ftp)# server
	dnRouter(cfg-system-ftp-server)#

	nRouter(cfg-system-ftp-server)#  vrf default
	dnRouter(cfg-ftp-server-vrf)# !
	dnRouter(cfg-system-ftp-server)#
	dnRouter(cfg-system-ftp-server)# vrf mgmt0
	dnRouter(cfg-ftp-server-vrf)# !
	dnRouter(cfg-system-ftp-server)#




**Removing Configuration**

To revert the router-id to default:
::

	dnRouter(cfg-system-ftp-server)# no vrf default

.. **Help line:** Configure FTP VRF for client list.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+
