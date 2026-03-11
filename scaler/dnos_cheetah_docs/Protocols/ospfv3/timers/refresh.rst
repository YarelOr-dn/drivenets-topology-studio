protocols ospfv3 timers refresh
-------------------------------

**Minimum user role:** operator

OSPFV3 link states have an age, indicating whether the link state is still valid. When the link state reaches the maximum age, it is discarded. During the aging process, the originating router periodically sends a refresh packet to refresh the link state and keep it from expiring.
To configure the refresh timer:

**Command syntax: refresh [refresh-timer]**

**Command mode:** config

**Hierarchies**

- protocols ospfv3 timers

**Parameter table**

+---------------+----------------------------------------------------+-----------+---------+
| Parameter     | Description                                        | Range     | Default |
+===============+====================================================+===========+=========+
| refresh-timer | Sets the time of the OSPF link-state refresh timer | 1800-2700 | 1800    |
+---------------+----------------------------------------------------+-----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols ospfv3
    dnRouter(cfg-protocols-ospfv3)# timers refresh 2000


**Removing Configuration**

To revert to the default timer value
::

    dnRouter(cfg-protocols-ospfv3)# no timers refresh

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
