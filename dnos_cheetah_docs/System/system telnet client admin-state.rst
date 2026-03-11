system telnet client admin-state
--------------------------------

**Minimum user role:** operator

To configure the admin-state for the telnet client.

**Command syntax: client admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- system telnet client

**Note**

- Active sessions are immediately disconnected when configuration is set to "disabled"

.. - no command returns the state to default.

	- Active sessions are immediately disconnected upon configuration of "disabled".

**Parameter table**

+-------------+---------------------------------------+----------+----------+
| Parameter   | Description                           | Range    | Default  |
+=============+=======================================+==========+==========+
| admin-state | The admin-state for the telnet client | Enabled  | Enabled  |
|             |                                       | Disabled |          |
+-------------+---------------------------------------+----------+----------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# telnet
	dnRouter(cfg-system-telnet)# client admin-state enabled
	dnRouter(cfg-system-telnet)# client admin-state disabled



**Removing Configuration**

To revert the router-id to default:
::

	dnRouter(cfg-system-telnet)# no client admin-state

.. **Help line:** Enabled/Disabled telnet client functionality on system.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+

