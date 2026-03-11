protocols ldp multipoint load-split downstream-rebalancing-timer
----------------------------------------------------------------

**Minimum user role:** operator

To configure the mLDP load split downstream rebalancing timer:


**Command syntax: downstream-rebalancing-timer [downstream-rebalancing-timer]**

**Command mode:** config

**Hierarchies**

- protocols ldp multipoint load-split

**Parameter table**

+------------------------------+-------------------------------------------------------------------------+--------+---------+
| Parameter                    | Description                                                             | Range  | Default |
+==============================+=========================================================================+========+=========+
| downstream-rebalancing-timer | The timer for global mLDP LSPs rebalancing across downstream interfaces | 1-3600 | 60      |
+------------------------------+-------------------------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ldp
    dnRouter(cfg-protocols-ldp)# multipoint
    dnRouter(cfg-protocols-ldp-mldp)# load-split
    dnRouter(cfg-ldp-mldp-ls)# downstream-rebalancing-timer 600


**Removing Configuration**

To revert the mLDP load split downstream rebalancing timer to its default value: 
::

    dnRouter(cfg-ldp-mldp-ls)# no downstream-rebalancing-timer

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
