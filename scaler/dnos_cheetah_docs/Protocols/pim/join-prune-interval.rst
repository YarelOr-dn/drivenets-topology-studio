protocols pim join-prune-interval
---------------------------------

**Minimum user role:** operator

To set the join-prune-interval value for outgoing PIM packets:

**Command syntax: join-prune-interval [join-prune-interval]**

**Command mode:** config

**Hierarchies**

- protocols pim

**Parameter table**

+---------------------+----------------------------------------------------------------------------------+--------+---------+
| Parameter           | Description                                                                      | Range  | Default |
+=====================+==================================================================================+========+=========+
| join-prune-interval | Periodic interval between Join/Prune messages. If 'infinity' or 'not-set' is     | 10-600 | 60      |
|                     | used, no periodic Join/Prune messages are sent. The hold-time associated with    |        |         |
|                     | the PIM-Join message is 3.5 times the pim join-prune-interval                    |        |         |
+---------------------+----------------------------------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)# join-prune-interval 180
    dnRouter(cfg-protocols-pim)#


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-pim)# no join-prune-interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
