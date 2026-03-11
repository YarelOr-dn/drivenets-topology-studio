ldp graceful-restart recovery-time
----------------------------------

**Minimum user role:** operator

When a router restarts, its peer helper will wait for no longer than the "reconnect time" for the connection to reestablish. Once the connection has reestablished (which must occur before the reconnect-time expires), both peers inform each other of the duration the peer must maintain the LDP bindings in stale state before it is removed from the FIB - this is the Fault Tolerance TLV recovery time where both peers inform each other during the session reinitialization. Both LDP peers wait until the end of the recovery time during which the LDP peers exchange label mappings and restart gracefully before purging the LDP information from both helper and restarting router. During the recovery time, both LDP peers maintain the LDP forwarding information and keep forwarding while exchanging label mappings and clearing the stale marking from refreshed states. Only those LDP entries that remained stale after the recovery time are deleted and cleared from the FIB.
To configure the LDP graceful restart recovery time:

**Command syntax: recovery-time [recovery-time]**

**Command mode:** config

**Hierarchies**

- protocols ldp graceful-restart 

.. **Note**

.. - recovery-time - time to wait for recovery after graceful-restart

.. - 'no recovery-time' - returns recovery-time to its default configuration

.. - 'no graceful-restart recovery-time' reverts recovery-time to its default value

**Parameter table**

+------------------+--------------------------------------------------------------------+--------------+-------------+
|                  |                                                                    |              |             |
| Parameter        | Description                                                        | Range        | Default     |
+==================+====================================================================+==============+=============+
|                  |                                                                    |              |             |
| recovery-time    | Time (in seconds) to wait for recovery after a graceful-restart    | 30..1800     | 120         |
+------------------+--------------------------------------------------------------------+--------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# ldp
	dnRouter(cfg-protocols-ldp)# graceful-restart
	dnRouter(cfg-protocols-ldp-gr)# recovery-time 140

**Removing Configuration**

To revert to the default value:
::

	dnRouter(cfg-protocols-ldp-gr)# no recovery-time

	dnRouter(cfg-protocols-ldp)# no graceful-restart recovery-time

.. **Help line:** Configure LDP Graceful Restart recovery time

**Command History**

+-----------+-----------------------+
| Release   | Modification          |
+===========+=======================+
| 13.0      | Command introduced    |
+-----------+-----------------------+