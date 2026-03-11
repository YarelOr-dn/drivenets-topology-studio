protocols ldp multipoint make-before-break timeout
--------------------------------------------------

**Minimum user role:** operator

To configure the timeout (in seconds) for a downstream node to await acknowledgement of MBB notifications from upstream nodes:


**Command syntax: timeout [mbb-timeout]**

**Command mode:** config

**Hierarchies**

- protocols ldp multipoint make-before-break

**Parameter table**

+-------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter   | Description                                                                      | Range | Default |
+=============+==================================================================================+=======+=========+
| mbb-timeout | The timeout (in seconds) for a downstream node to await acknowledgement of MBB   | 1-600 | 30      |
|             | notifications from upstream nodes. Even if an MBB acknowledgment is not received |       |         |
|             | for a point-to-multipoint LSP before the specified timeout period expires, the   |       |         |
|             | label-switching router (LSR) performs an MBB switchover from the old LSR to the  |       |         |
|             | new upstream LSR.                                                                |       |         |
+-------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ldp
    dnRouter(cfg-protocols-ldp)# multipoint
    dnRouter(cfg-protocols-ldp-mldp)# mbb
    dnRouter(cfg-ldp-mldp-mbb)# timeout 60


**Removing Configuration**

To revert the mLDP MBB timeout to its default value: 
::

    dnRouter(cfg-ldp-mldp-mbb)# no timeout

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
