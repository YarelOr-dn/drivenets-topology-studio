ldp address-family discovery targeted hello
-------------------------------------------

**Minimum user role:** operator

This command allows you to set the frequency that targeted hello messages will be sent and the duration of the hold time for LDP hello adjacency:

**Command syntax: hello interval [interval] holdtime [holdtime]**

**Command mode:** config

**Hierarchies**

- protocols ldp address-family discovery-targeted

.. **Note:**

	- holdtime must be at least three times greater than interval

	- 'no hello' - returns interval and holdtime to default values

**Parameter table**

+---------------------+-----------------------------------------------------------------------------------------------------------------------------+-------------+---------------+
|                     |                                                                                                                             |             |               |
| Parameter           | Description                                                                                                                 | Range       | Default       |
+=====================+=============================================================================================================================+=============+===============+
|                     |                                                                                                                             |             |               |
| hello interval      | The interval (in seconds) that hello messages will be sent                                                                  | 1..21845    | 10 seconds    |
+---------------------+-----------------------------------------------------------------------------------------------------------------------------+-------------+---------------+
|                     |                                                                                                                             |             |               |
| session-holdtime    | The period of time (in seconds) in which a session will go down if no hellos have been received after the timer expires.    | 3..65535    | 90 seconds    |
+---------------------+-----------------------------------------------------------------------------------------------------------------------------+-------------+---------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# ldp
	dnRouter(cfg-protocols-ldp)# address-family ipv4-unicast
	dnRouter(cfg-protocols-ldp-afi)# discovery targeted
	dnRouter(cfg-ldp-afi-disc-tar)# hello interval 15 holdtime 45

**Removing Configuration**

To return the interval and holdtime to their default values:
::

	dnRouter(cfg-ldp-afi-disc-tar)# no hello

.. **Help line:** Set targeted hello parameters

**Command History**

+-----------+-----------------------+
| Release   | Modification          |
+===========+=======================+
| 15.0      | Command introduced    |
+-----------+-----------------------+