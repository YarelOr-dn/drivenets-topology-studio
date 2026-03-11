ldp graceful-restart admin-state
--------------------------------

**Minimum user role:** operator

To enable/disable LDP graceful restart:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols ldp graceful-restart 

.. **Note**

.. - graceful-restart is disabled by default

.. - 'no admin-state' returns graceful restart admin-state to default (disabled)

**Parameter table**

+----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------+-------------+
|                |                                                                                                                                                                                                                                                                                                                                                                                                        |             |             |
| Parameter      | Description                                                                                                                                                                                                                                                                                                                                                                                            | Range       | Default     |
+================+========================================================================================================================================================================================================================================================================================================================================================================================================+=============+=============+
|                |                                                                                                                                                                                                                                                                                                                                                                                                        |             |             |
| admin-state    | Sets the administrative state of the graceful restart feature. When enabled, LDP will continue forwarding traffic for a grace period during a failure, in the case that both peers exchange Fault Tolerance TLV in the   initialization message, and both peers declare support in graceful restart   informing the peer of the reconnect time they expect him to wait after losing   neighborship.    | Enabled     | Disabled    |
|                |                                                                                                                                                                                                                                                                                                                                                                                                        |             |             |
|                |                                                                                                                                                                                                                                                                                                                                                                                                        | Disabled    |             |
+----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------+-------------+

**Example:**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# ldp
	dnRouter(cfg-protocols-ldp)# graceful-restart
	dnRouter(cfg-protocols-ldp-gr)# admin-state enabled

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# ldp
	dnRouter(cfg-protocols-ldp)# graceful-restart
	dnRouter(cfg-protocols-ldp-gr)# admin-state disabled

**Removing Configuration**

To revert to the default value:
::

	dnRouter(cfg-protocols-ldp-gr)# no admin-state

.. **Help line:** Configure LDP Graceful Restart admin state.

**Command History**

+-----------+-----------------------+
| Release   | Modification          |
+===========+=======================+
| 13.0      | Command introduced    |
+-----------+-----------------------+