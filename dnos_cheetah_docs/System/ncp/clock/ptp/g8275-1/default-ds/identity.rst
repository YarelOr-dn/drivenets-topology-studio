system ncp clock ptp g8275-1 default-ds identity
------------------------------------------------

**Minimum user role:** operator

Set the PTP clock identity. An IEEE-1588 defined octet array used to uniquely represent the identity of a PTP clock.

**Command syntax: identity [identity]**

**Command mode:** config

**Hierarchies**

- system ncp clock ptp g8275-1 default-ds

**Parameter table**

+-----------+------------------------------+-------+---------+
| Parameter | Description                  | Range | Default |
+===========+==============================+=======+=========+
| identity  | Sets the PTP clock identity. | \-    | \-      |
+-----------+------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ncp 7
    dnRouter(cfg-system-ncp-7)# clock
    dnRouter(cfg-system-ncp-7-clk)# ptp
    dnRouter(cfg-system-ncp-7-clk-ptp)# g8275-1
    dnRouter(cfg-system-ncp-7-clk-ptp-g8275-1)# default-ds
    dnRouter(cfg-system-ncp-7-clk-ptp-g8275-1)-default-ds)# identity a4:0c:c3:ff:fe:bf:2b:0


**Removing Configuration**

To revert the sync-option to its default value:
::

    dnRouter(cfg-system-ncp-7-clk-ptp-g8275-1)-default-ds)# no identity

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
