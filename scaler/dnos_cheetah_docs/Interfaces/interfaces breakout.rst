interfaces breakout
-------------------

**Minimum user role:** operator

1. NCP-40C port breakout
100GE ports 0..19 of each NCP-40c can be broken out into 4x10GE ports using an external breakout cable. When port 0 is broken out, port 21 is disabled, and similarly each 100GE port broken up disables one associated 100GE port, per the table below:

+-----------------+------------------------------+
| Port broken-out | Port disabled as a result    |
+=================+==============================+
| 0               | 21                           |
+-----------------+------------------------------+
| 1               | 20                           |
+-----------------+------------------------------+
| 2               | 23                           |
+-----------------+------------------------------+
| 3               | 22                           |
+-----------------+------------------------------+
| 4               | 25                           |
+-----------------+------------------------------+
| 5               | 24                           |
+-----------------+------------------------------+
| 6               | 27                           |
+-----------------+------------------------------+
| 7               | 26                           |
+-----------------+------------------------------+
| 8               | 29                           |
+-----------------+------------------------------+
| 9               | 28                           |
+-----------------+------------------------------+
| 10              | 31                           |
+-----------------+------------------------------+
| 11              | 30                           |
+-----------------+------------------------------+
| 12              | 33                           |
+-----------------+------------------------------+
| 13              | 32                           |
+-----------------+------------------------------+
| 14              | 35                           |
+-----------------+------------------------------+
| 15              | 34                           |
+-----------------+------------------------------+
| 16              | 37                           |
+-----------------+------------------------------+
| 17              | 36                           |
+-----------------+------------------------------+
| 18              | 39                           |
+-----------------+------------------------------+
| 19              | 38                           |
+-----------------+------------------------------+

The 4 10GE ports are named ge10-<f>/<n>/<p>/<b>, where b is the breakout port 0..3, with the same forwarder (f), slot number (n) and port (p) of their parent. For example ge100-1/0/2 is broken up to ge10-1/0/2/0, ge10-1/0/2/1, ge10-1/0/2/2 and ge10-1/0/2/3.

The operative state of both the breakout port and the associated disabled port will be set to 'not present'.
When a port is broken-out, the configuration of the port and the associated disabled port are erased and set to default. The 10GE ports configuration is erased from the database once a 'no breakout' command is issued, and the 10GE ports will be removed completely, i.e. they will not be present in 'show interfaces' output or its equivalent.

The breakout command will fail validation if either of the following conditions are not met:
- Both the broken out port and the associated port admin status must be down.
- Both ports must not be members of a LAG. The ports must be removed from the LAG prior to breakout.
- Both ports must not be configured to run any routing or control protocol, e.g. ISIS, OSPF, RSVP, LACP, etc. The protocl configuration must be removed prior to breakout.

The 'no breakout' command will fail validation if either of the following conditions are not met:
- All 4 10GE ports admin status must be down.
- All 4 10GE ports must not be members of a LAG. The ports must be removed from the LAG prior to cancelling breakout.
- All 4 10GE ports must not be configured to run any routing or control protocol, e.g. ISIS, OSPF, RSVP, LACP, etc. The protocl configuration must be removed prior to breakout.

2. NCP-36CD(-S) and NCP-36CD-S-SA port breakout
400GE ports 0..35 of each NCP-36cd can be broken out into 4x100GE, 2x200GE or 2x100GE ports using an external breakout cable. All 400GE NIF ports can breakout to 4x100GE 2x200GE or 2x100GE. No sacrificed ports. The naming convention is similar to 10GE breakout: ge<100/200>-<f>/<n>/<p>/<b>, where b is the breakout port 0..3 (See above for details). All other definitions as detailed above apply, apart from sacrificed ports.

3. NCP-32CD port breakout
400GE ports 0..31 of each NCP-32CD can be broken out into 4x100GE or 2x100GE ports using an external breakout cable. All 400GE NIF ports can breakout to 4x100GE or 2x100GE. No sacrificed ports. The naming convention is similar to 10GE breakout: ge<100/200>-<f>/<n>/<p>/<b>, where b is the breakout port 0..3 (See above for details). All other definitions as detailed above apply, apart from sacrificed ports.

**Command syntax: breakout [breakout-mode]**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The maximal number of 10G port in any cluster size is limited to 80 ports.

- No limitation on the number of 100G/200G breakout ports.

**Parameter table**

+---------------+-------------------------------+-------------+---------+
| Parameter     | Description                   | Range       | Default |
+===============+===============================+=============+=========+
| breakout-mode | The method used for breakout. | | none      | none    |
|               |                               | | 10g-4x    |         |
|               |                               | | 100g-4x   |         |
|               |                               | | 200g-2x   |         |
|               |                               | | 100g-2x   |         |
|               |                               | | 400g-2x   |         |
+---------------+-------------------------------+-------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-0/0/0
    dnRouter(cfg-if-ge100-0/0/0)# breakout 10g-4x

    dnRouter# configure
    dnRouter(cfg)# interfaces ge100-0/0/0 breakout 10g-4x
    dnRouter(cfg)# no interfaces ge100-0/0/0 breakout 10g-4x
    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge400-0/0/0
    dnRouter(cfg-if-ge400-0/0/0)# breakout 100g-4x
    dnRouter(cfg-if-ge400-0/0/0)# no breakout

    dnRouter# configure
    dnRouter(cfg)# interfaces ge400-0/0/0 breakout 100g-4x

    dnRouter(cfg)# no interfaces ge400-0/0/0 breakout 100g-4x
    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge400-0/0/0
    dnRouter(cfg-if-ge400-0/0/0)# breakout 200g-2x
    dnRouter(cfg-if-ge400-0/0/0)# no breakout

    dnRouter# configure
    dnRouter(cfg)# interfaces ge400-0/0/0 breakout 200g-2x
    dnRouter(cfg)# no interfaces ge400-0/0/0 breakout 200g-2x
    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge400-0/0/0
    dnRouter(cfg-if-ge400-0/0/0)# breakout 100g-2x
    dnRouter(cfg-if-ge400-0/0/0)# no breakout

    dnRouter# configure
    dnRouter(cfg)# interfaces ge400-0/0/0 breakout 100g-2x
    dnRouter(cfg)# no interfaces ge400-0/0/0 breakout 100g-2x


**Removing Configuration**

To remove an interface breakout:
::

    dnRouter(cfg-if-ge100-0/0/0)# no breakout

**Command History**

+---------+------------------------------------------------------+
| Release | Modification                                         |
+=========+======================================================+
| 12.0    | Command introduced                                   |
+---------+------------------------------------------------------+
| 16.1    | Added support for 400GE interface breakout           |
+---------+------------------------------------------------------+
| 17.0    | Added support for 400GE to 2x200G interface breakout |
+---------+------------------------------------------------------+
| „       | Added support for 400GE to 2x100G interface breakout |
+---------+------------------------------------------------------+
