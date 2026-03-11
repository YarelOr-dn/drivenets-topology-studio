system ftp server admin-state
-----------------------------

**Minimum user role:** operator

Use the following command to enable/disable configuration for FTP server admin-state:

**Command syntax: server admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- system ftp


**Note**

- The 'no admin-state' returns the state to default.

- Active sessions are immediately disconnected upon configuration of 'disabled'.

- Only new sessions can not be established.

The FTP server supports connections over the following interfaces:

- physical

- bundle

- sub-interface (physical.vlan, bundle.vlan)

- loopback

- Support FTP for default VRF only.

.. - No command returns the state to default.

	- Active sessions are immediately disconnected upon configuration of "disabled".

	- Only new sessions can not be established

	- FTP server supports connections on the following interfaces

	   - physical

	   - bundle

	   - sub-interface(physical.vlan, bundle.vlan)

	   - loopback

	   - Support FTP for default VRF only

**Parameter table**

+-------------+------------------------------------------------+----------+---------+
| Parameter   | Description                                    | Range    | Default |
+=============+================================================+==========+=========+
| admin-state | Set the administrative state of the FTP server | Enabled  | Enabled |
|             |                                                | Disabled |         |
+-------------+------------------------------------------------+----------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# ftp
	dnRouter(cfg-system-ftp)# server
	dnRouter(cfg-system-ftp-server)# admin-state disable

**Removing Configuration**

To revert the router-id to default:
::

	dnRouter(cfg-system-ftp-server)# no admin-state

.. **Help line:** enabled/disabled ftp server functionality on system.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
