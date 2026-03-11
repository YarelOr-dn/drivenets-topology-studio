ldp address-family session holdtime
-----------------------------------

**Minimum user role:** operator

Set the default LDP TCP session holdtime (in seconds) per address-family:

**Command syntax: session holdtime [session-holdtime]**

**Command mode:** config

**Hierarchies**

- protocols ldp address-family

.. **Note:**

.. - 'no' command restores the session hold time to its default value

.. - When configuring the LDP graceful restart process in a network with multiple links between the local LSR and same neighbor, make sure that graceful restart is activated on the session before any hello adjacency times out in case of neighbor control plane failures. One way of achieving this is by configuring a lower session hold time between neighbors such that session timeout occurs before hello adjacency timeout. It is recommended to set LDP session hold time that satisfies: Session Holdtime <= (Hello holdtime - Hello interval) * 3.   This means that for default values of 15 seconds and 5 seconds for link Hello holdtime and interval respectively, session hold time should be set to 30 seconds at most.

**Parameter table**

+---------------------+------------------------------------------------------------------------------------------------------------------------------------------------+----------------------+----------------+
|                     |                                                                                                                                                |                      |                |
| Parameter           | Description                                                                                                                                    | Range                | Default        |
+=====================+================================================================================================================================================+======================+================+
|                     |                                                                                                                                                |                      |                |
| session-holdtime    | The period of time (in seconds) in which a discovered LDP neighbor is remembered without receiving an LDP Hello message from the neighbor.     | 15..65535 seconds    | 180 seconds    |
+---------------------+------------------------------------------------------------------------------------------------------------------------------------------------+----------------------+----------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# ldp
	dnRouter(cfg-protocols-ldp)# address-family ipv4-unicast
	dnRouter(cfg-protocols-ldp-afi)# session holdtime 60

**Removing Configuration**

To revert to the default session holdtime:
::

	dnRouter(cfg-protocols-ldp-afi)# no session holdtime

.. **Help line:** Sets the default LDP session holdtime.

**Command History**

+-----------+-----------------------+
| Release   | Modification          |
+===========+=======================+
| 6.0       | Command introduced    |
+-----------+-----------------------+