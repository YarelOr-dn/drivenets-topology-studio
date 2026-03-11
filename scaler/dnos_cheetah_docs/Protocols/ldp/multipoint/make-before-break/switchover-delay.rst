protocols ldp multipoint make-before-break switchover-delay
-----------------------------------------------------------

**Minimum user role:** operator

To configure the switchover delay in seconds for a point-to-multipoint LSP from the old LSR to the new upstream LSR:


**Command syntax: switchover-delay [switchover-delay]**

**Command mode:** config

**Hierarchies**

- protocols ldp multipoint make-before-break

**Parameter table**

+------------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter        | Description                                                                      | Range | Default |
+==================+==================================================================================+=======+=========+
| switchover-delay | Switchover delay in seconds for a point-to-multipoint LSP from the old LSR to    | 1-600 | 30      |
|                  | the new upstream LSR. If an MBB acknowledgment is received on a point of local   |       |         |
|                  | repair (PLR) router, the PLR waits for the specified seconds to switch its       |       |         |
|                  | upstream LSR from the old LSR to the new LSR.                                    |       |         |
+------------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ldp
    dnRouter(cfg-protocols-ldp)# multipoint
    dnRouter(cfg-protocols-ldp-mldp)# mbb
    dnRouter(cfg-ldp-mldp-mbb)# switchover-delay 10


**Removing Configuration**

To revert the mLDP MBB switchover delay to its default value: 
::

    dnRouter(cfg-ldp-mldp-mbb)# no switchover-delay

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
