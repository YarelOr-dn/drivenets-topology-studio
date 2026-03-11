protocols msdp sa-hold-time
---------------------------

**Minimum user role:** operator

When a new MSDP SA TLV is accepted, the router caches the entry and sets its hold timer to sa-hold-time. If the MSDP SA TLV with the same (S,G,RP) is revived before the timer expires, its hold time is reset to sa-hold-time. In any other case, the entry is removed from the cache.

**Command syntax: sa-hold-time [sa-hold-time]**

**Command mode:** config

**Hierarchies**

- protocols msdp

**Note**
- The hold-time timer must be greater than the keep-alive timer. The user is warned in case the keep-alive timer is greater or equal to hold-time.

**Parameter table**

+--------------+--------------------------------------------+----------+---------+
| Parameter    | Description                                | Range    | Default |
+==============+============================================+==========+=========+
| sa-hold-time | Sets the MSDP received SA state hold time. | 150-3600 | 150     |
+--------------+--------------------------------------------+----------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# msdp
    dnRouter(cfg-protocols-msdp)# sa-hold-time 250


**Removing Configuration**

To revert the sa-hold-time to its default value:
::

    dnRouter(cfg-protocols-msdp)# no sa-hold-time

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
