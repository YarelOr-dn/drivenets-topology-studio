ldp interface discovery hello
-----------------------------

**Minimum user role:** operator

You can set the LDP hello timers per interface. This command overrides the default hello timers for a specified interface:

**Command syntax: discovery hello interval [interval] holdtime [holdtime]**

**Command mode:** config

**Hierarchies**

- protocols ldp address-family interface

**Note**

- The holdtime must be at least three times greater than interval, if the interval is 15, the holdtime must be at least 45 or greater.

- If you do not set discovery parameters, the default values will apply. The default values for this command are the current values of the LDP address-family discovery hello configuration. 

**Parameter table**

+---------------+-----------------------------------------------------------------------------------------------------------------------+-------------+---------------+
|               |                                                                                                                       |             |               |
| Parameter     | Description                                                                                                           | Range       | Default       |
+===============+=======================================================================================================================+=============+===============+
|               |                                                                                                                       |             |               |
| interval      | The period of time (in seconds) between the sending of consecutive Hello messages.                                    | 1..21845    | 5 seconds     |
+---------------+-----------------------------------------------------------------------------------------------------------------------+-------------+---------------+
|               |                                                                                                                       |             |               |
| holdtime      | The period of time a discovered LDP neighbor is remembered without receipt of an LDP Hello message from the neighbor. | 3..65535    | 15 seconds    |
|               |                                                                                                                       |             |               |
+---------------+-----------------------------------------------------------------------------------------------------------------------+-------------+---------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# ldp
	dnRouter(cfg-protocols-ldp)# address-family ipv4-unicast
	dnRouter(cfg-protocols-ldp-afi)# interface bundle-2
	dnRouter(cfg-protocols-ldp-afi-if)# discovery hello interval 20 holdtime 60

**Removing Configuration**

To revert all discovery interval and holdtime values of the interface to their default value:
::

	dnRouter(cfg-protocols-ldp-afi-if)# no discovery hello

.. **Help line:** Sets the LDP hello timers per interface.

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