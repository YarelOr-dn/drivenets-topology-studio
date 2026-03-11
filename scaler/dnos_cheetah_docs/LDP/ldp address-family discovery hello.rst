ldp address-family discovery hello
----------------------------------

**Minimum user role:** operator

This command sets how often hello messages are sent and the time (in seconds) in which a session is maintained in the absence of LDP messages from the neighbor (hello adjacency):

**Command syntax: discovery hello interval [interval] holdtime [holdtime]**

**Command mode:** config

**Hierarchies**

- protocols ldp address-family

**Note**

- The holdtime must be at least three times greater than interval, if the interval is 15, the holdtime must be at least 45 or greater.

**Parameter table**

+-------------------+--------------------------------------------------------------------------------------------------------------------+-------------+---------------+
|                   |                                                                                                                    |             |               |
| Parameter         | Description                                                                                                        | Range       | Default       |
+===================+====================================================================================================================+=============+===============+
|                   |                                                                                                                    |             |               |
| hello interval    | The interval (in seconds) in which hello packets are sent.                                                         | 1..21845    | 5 seconds     |
+-------------------+--------------------------------------------------------------------------------------------------------------------+-------------+---------------+
|                   |                                                                                                                    |             |               |
| hello holdtime    | The period of time (in seconds) in which a session is maintained in the absence of LDP messages from the neighbor. | 3..65535    | 15 seconds    |
|                   |                                                                                                                    |             |               |
+-------------------+--------------------------------------------------------------------------------------------------------------------+-------------+---------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# ldp
	dnRouter(cfg-protocols-ldp)# address-family ipv4-unicast
	dnRouter(cfg-protocols-ldp-afi)# discovery hello interval 15 holdtime 45

**Removing Configuration**

To revert to the default configuration:
::

	dnRouter(cfg-protocols-ldp-afi)# no discovery hello

.. **Help line:** Set the default LDP discovery hello timers per address-family.

**Command History**

+-------------+---------------------------------------------------------------+
|             |                                                               |
| Release     | Modification                                                  |
+=============+===============================================================+
|             |                                                               |
| 6.0         | Command introduced                                            |
+-------------+---------------------------------------------------------------+
|             |                                                               |
| 13.0        | Updated range values for hello interval and hello holdtime    |
+-------------+---------------------------------------------------------------+
