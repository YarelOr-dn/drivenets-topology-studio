system telnet server vrf
------------------------

**Minimum user role:** operator

To set Telnet client-list attachment per VRF:

**Command syntax: server vrf [vrf-name]**

**Command mode:** config

**Hierarchies**

- system telnet server

**Note**

- Notice the change in prompt.

.. -  vrf definition level is introduced for attaching client-list.

	- vrf "default" represents the in-band management, while vrf "mgmt0" represents the out-of-band management.

	- no command deletes the configuration under the specific vrf.

**Parameter table**

+-----------+---------------------------------------------------------------------------------+---------------------+---------+
| Parameter | Description                                                                     | Range               | Default |
+===========+=================================================================================+=====================+=========+
| vrf-name  | Allows to define separate Telnet client-lists per VRF (in-band and out-of-band) | default - in-band   | \-      |
|           |                                                                                 | mgmt0 - out-of-band |         |
+-----------+---------------------------------------------------------------------------------+---------------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# telnet
	dnRouter(cfg-system-telnet)# server vrf default
	dnRouter(cfg-telnet-server-vrf)# !
	dnRouter(cfg-system-telnet)#
	dnRouter(cfg-system-telnet)# server vrf mgmt0
	dnRouter(cfg-telnet-server-vrf)# !
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-telnet-server)# no admin-state

.. **Help line:** Enabled/Disabled telnet client functionality on system.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+


