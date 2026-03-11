system telnet server admin-state
--------------------------------

**Minimum user role:** operator

The Telnet server supports connections on the following interfaces:

This command is applicable to the following interfaces:

- physical interfaces

- logical interfaces (sub-interfaces)

- bundle interfaces

- bundle sub-interfaces

- loopback interfaces

- mgmt-ncc interfaces

**Command syntax: server admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

-  system telnet server

**Note**

- Telnet is supported on the both default and mgmt0 VRFs.

- Active sessions are not disconnected when the configuration is set to "disabled".

.. - no command returns the admin-state to default value.

	- Active sessions are not disconnected upon configuration of "disable".

	- Only new sessions can not be established

	- Telnet server supports connections on the following interfaces

	- physical

	- bundle

	- sub-interface(physical.vlan, bundle.vlan)

	- loopback

	- mgmt

	- Support Telnet for default VRF only

**Parameter table**

+-------------+------------------------------------------------+----------+----------+
| Parameter   | Description                                    | Range    | Default  |
+=============+================================================+==========+==========+
| admin-state | The administrative state for the telnet server | Enabled  | Disabled |
|             |                                                | Disabled |          |
+-------------+------------------------------------------------+----------+----------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# telnet
	dnRouter(cfg-system-telnet)# server
	dnRouter(cfg-system-telnet-server)# admin-state disable
	
	

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


