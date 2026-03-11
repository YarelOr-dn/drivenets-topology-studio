system netconf
--------------

**Minimum user role:** operator

To configure a Netconf server:

**Command syntax: parameters [parameters-value]**

**Command mode:** config

**Hierarchies**

- system netconf

.. **Note**

 - The no command removes the Netconf configuration.

**Parameter table**

+------------------+-------------------------------------------------------------+---------------------+------------+
| Parameter        | Description                                                 | Range               | Default    |
+------------------+-------------------------------------------------------------+---------------------+------------+
| admin-state      | The administrative state of the server                      | enabled             | enabled    |
|                  |                                                             |                     |            |
|                  |                                                             | disabled            |            |
+------------------+-------------------------------------------------------------+---------------------+------------+
| max-sessions     | The maximum number of concurrent sessions                   | 1..6                | 6          |
+------------------+-------------------------------------------------------------+---------------------+------------+
| session-timeout  | The maximum amount of time allowed for a session to be idle | 0..90 (minutes)     | 30 minutes |
+------------------+-------------------------------------------------------------+---------------------+------------+
| class-of-service | The class-of-service for all outgoing Netconf sessions      | 0..56               | 0          |
+------------------+-------------------------------------------------------------+---------------------+------------+
| vrf-name         | default, mgmt0, non-default-vrf                             |                     |            |
+------------------+-------------------------------------------------------------+---------------------+------------+
| client-list      | The client IP-addresses for Netconf sessions                | A.B.C.D/x           | \-         |
|                  |                                                             |                     |            |
|                  |                                                             | ipv6-address-format |            |
+------------------+-------------------------------------------------------------+---------------------+------------+


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# netconf
	dnRouter(cfg-system-netconf)# admin-state enabled

**Removing Configuration**

To remove the Netconf configuration:
::

	dnRouter(cfg-system)# no netconf


.. **Help line:** Configure NETCONF server

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
