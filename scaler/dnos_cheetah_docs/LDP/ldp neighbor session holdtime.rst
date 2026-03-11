ldp neighbor session holdtime
-----------------------------

**Minimum user role:** operator

To change the session holdtime for the neighbor:

**Command syntax: session holdtime [session-holdtime]**

**Command mode:** config

**Hierarchies**

- protocols ldp neighbor

..
	**Note**

	- Default value for neighbor session holdtime is derived from the configured address-family session holdtime.

**Parameter table**

+------------------+--------------------------------------------------------------------------------------------------------------------+-----------+------------------------------------------+
| Parameter        | Description                                                                                                        | Range     | Default                                  |
+==================+====================================================================================================================+===========+==========================================+
| session-holdtime | The period of time (in seconds) in which a session is maintained in the absence of LDP messages from the neighbor. | 15..65535 | Same as address-family session-holdtime. |
+------------------+--------------------------------------------------------------------------------------------------------------------+-----------+------------------------------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# ldp
	dnRouter(cfg-protocols-ldp)# neighbor 21.1.34.1
	dnRouter(cfg-protocols-ldp-neighbor)# session holdtime 1000

**Removing Configuration**

To revert to the default session holdtime:
::

	dnRouter(cfg-protocols-ldp-neighbor)# no session holdtime

.. **Help line:** Sets the session holdtime for a specific neighbor.

**Command History**

+-----------+-----------------------+
| Release   | Modification          |
+===========+=======================+
| 13.0      | Command introduced    |
+-----------+-----------------------+