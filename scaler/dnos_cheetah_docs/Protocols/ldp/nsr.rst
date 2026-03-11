protocols ldp nsr
-----------------

**Minimum user role:** operator

LDP nonstop routing (NSR) enables an LDP speaker to maintain the LDP session's state while undergoing switchover at the CPU level (e.g. NCC switchover).
Unlike LDP graceful-restart (GR), which requires both LDP ends to support the GR capability and logic, NSR is transparent, and the other end of the LDP session is unaware of the NSR process.

While LDP works with NSR, LDP continue to support as a helper for neighbor GR.

The LDP process (ldpd) running on the active NCC, saves (in the NSR DB) all the information required for recovering from an LDP failure and for providing nonstop routing (including LDP TCP session information and any advertised and received prefix<->label).
The NSR DBs, located on both active and standby NCCs, are regularly synchronized. In the event of a switchover/failover, ldpd starts on the standby NCC and recovers the TCP and LDP session parameters from the NSR-DB in the standby NCC.

To enable/disable the LDP NSR feature:

**Command syntax: nsr [nsr]**

**Command mode:** config

**Hierarchies**

- protocols ldp

**Note**

- LDP NSR cannot be enabled together with LDP Graceful-Restart.

**Parameter table**

+-----------+-----------------------------------------+--------------+---------+
| Parameter | Description                             | Range        | Default |
+===========+=========================================+==============+=========+
| nsr       | The admin-state of LDP non-stop-routing | | enabled    | enabled |
|           |                                         | | disabled   |         |
+-----------+-----------------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ldp
    dnRouter(cfg-protocols-ldp)# nsr enabled

    dnRouter(cfg-protocols-ldp)# nsr disabled


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-ldp)# no nsr

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
