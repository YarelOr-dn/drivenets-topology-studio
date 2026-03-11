protocols rsvp timers refresh-multiplier
----------------------------------------

**Minimum user role:** operator

The refresh-multiplier determines the number of messages that are allowed to be missed before a specific state is declared stale and the RSVP session is terminated. This command works together with the refresh-interval command (see  "rsvp timers refresh-interval".

The specific state is declared stale if a state message is not received refresh-interval x refresh-multiplier.

To configure the refresh-multiplier:

**Command syntax: refresh-multiplier [refresh-multiplier]**

**Command mode:** config

**Hierarchies**

- protocols rsvp timers

**Parameter table**

+--------------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter          | Description                                                                      | Range | Default |
+====================+==================================================================================+=======+=========+
| refresh-multiplier | set the number of messages that can be lost before a particular state is         | 1-255 | 3       |
|                    | declared                                                                         |       |         |
+--------------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# timers
    dnRouter(cfg-protocols-rsvp-timers)# refresh-multiplier 100


**Removing Configuration**

To revert to the refresh-multiplier to its default value:
::

    dnRouter(cfg-protocols-rsvp-timers)# no refresh-multiplier

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 9.0     | Command introduced |
+---------+--------------------+
