ldp graceful-restart reconnect-time
-----------------------------------

**Minimum user role:** operator

When the router gracefully restarts, its LDP peers wait a specific length of time before attempting to reestablish the LDP session. The restarting router is expected to resume sending LDP messages within this time frame.
To configure the LDP graceful restart reconnect time:

**Command syntax: reconnect-time [reconnect-time]**

**Command mode:** config

**Hierarchies**

- protocols ldp graceful-restart 

.. **Note**

.. - reconnect-time - time to wait to reestablish session after graceful-restart

.. - 'no graceful-restart reconnect-time' reverts reconnect-time to its default value

**Parameter table**

+-------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------+-------------+
|                   |                                                                                                                                                                                                                                                                                                          |             |             |
| Parameter         | Description                                                                                                                                                                                                                                                                                              | Range       | Default     |
+===================+==========================================================================================================================================================================================================================================================================================================+=============+=============+
|                   |                                                                                                                                                                                                                                                                                                          |             |             |
| reconnect-time    | Time (in seconds) the router expects the peer helper router to keep forwarding and for the connection reestablishment before it declares the neighborship lost. When the LDP session is initialized, the peers   exchange Fault Tolerance TLV where they inform each other of their reconnect   time.    | 30..300     | 60          |
+-------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# ldp
	dnRouter(cfg-protocols-ldp)# graceful-restart
	dnRouter(cfg-protocols-ldp-gr)# reconnect-time 70

**Removing Configuration**

To revert to the default value:
::

	dnRouter(cfg-protocols-ldp-gr)# no reconnect-time

	dnRouter(cfg-protocols-ldp)# no graceful-restart reconnect-time

.. **Help line:** Configure LDP Graceful Restart reconnect time.

**Command History**

+-----------+-----------------------+
| Release   | Modification          |
+===========+=======================+
| 13.0      | Command introduced    |
+-----------+-----------------------+