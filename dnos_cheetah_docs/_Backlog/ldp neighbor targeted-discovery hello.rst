ldp neighbor targeted-discovery hello
-------------------------------------

**Minimum user role:** operator

This command allows you to set the frequency that targeted hello messages will be sent for a targeted peer, and the duration of the hold time for LDP hello adjacency:

**Command syntax: targeted-discovery hello interval [interval] holdtime [holdtime]**

**Command mode:** config

**Hierarchies**

- protocols ldp neighbor

**Note**

- The holdtime must be at least three times greater than the interval.

..	- 'no targeted-discovery hello' - restores neigbhor LDP targeted-discovery hello interval and holdtime values to thier default values, inherited from address-family settings.

**Parameter table**

+---------------------+-----------------------------------------------------------------------------------------------------------------------------+-------------+---------------------------------------------------+
|                     |                                                                                                                             |             |                                                   |
| Parameter           | Description                                                                                                                 | Range       | Default                                           |
+=====================+=============================================================================================================================+=============+===================================================+
|                     |                                                                                                                             |             |                                                   |
| hello interval      | The interval (in seconds) in which hello messages will be sent                                                              | 1..21845    | ldp address-family discovery targeted interval    |
+---------------------+-----------------------------------------------------------------------------------------------------------------------------+-------------+---------------------------------------------------+
|                     |                                                                                                                             |             |                                                   |
| session-holdtime    | The period of time (in seconds) in which a session will go down if no hellos have been received after the timer expires     | 3..65535    | ldp address-family discovery targeted holdtime    |
+---------------------+-----------------------------------------------------------------------------------------------------------------------------+-------------+---------------------------------------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# ldp
	dnRouter(cfg-protocols-ldp)# neighbor 21.1.34.1
	dnRouter(cfg-protocols-ldp-neighbor)# targeted-discovery hello interval 15 holdtime 45

**Removing Configuration**

To revert the neigbhor LDP targeted-discovery hello interval and holdtime values to their default values, inherited from address-family settings.
::

	dnRouter(cfg-protocols-ldp-neighbor)# no targeted-discovery hello

.. **Help line:** Set the targeted LDP discovery hello timers per neighbor.

**Command History**

+-----------+-----------------------+
| Release   | Modification          |
+===========+=======================+
| 15.0      | Command introduced    |
+-----------+-----------------------+