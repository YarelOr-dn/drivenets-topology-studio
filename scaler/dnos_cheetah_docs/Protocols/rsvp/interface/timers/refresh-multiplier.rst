protocols rsvp interface timers refresh-multiplier
--------------------------------------------------

**Minimum user role:** operator

The refresh-multiplier determines the number of messages that are allowed to be missed before a specific state is declared stale and the RSVP session is terminated. This command works together with the refresh-interval command. The specific state is declared stale if a state message is not received refresh-interval x refresh-multiplier.
To configure the refresh-multiplier for the interface:

**Command syntax: refresh-multiplier [refresh-multiplier]**

**Command mode:** config

**Hierarchies**

- protocols rsvp interface timers

**Parameter table**

+--------------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter          | Description                                                                      | Range | Default |
+====================+==================================================================================+=======+=========+
| refresh-multiplier | the number of messages that can be lost before a particular state is declared    | 1-255 | \-      |
|                    | stale                                                                            |       |         |
+--------------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# interface bundle-1
    dnRouter(cfg-protocols-rsvp-if)# timers refresh-multiplier 100


**Removing Configuration**

To revert to the refresh-multiplier to its default value:
::

    dnRouter(cfg-protocols-rsvp-if)# no timers refresh-multiplier

**Command History**

+---------+----------------------------------------------------------+
| Release | Modification                                             |
+=========+==========================================================+
| 10.0    | Command introduced in rsvp interface configuration mode  |
+---------+----------------------------------------------------------+
