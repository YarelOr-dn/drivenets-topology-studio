protocols lacp interface mode
-----------------------------

**Minimum user role:** operator

LACP packets are exchanged between interfaces in the following modes:

•	Active: the interface initiates negotiation with another interface by sending LACP packets (LACPDUs).

•	Passive: the interface responds to LACP packets it receives but does not initiate LACP negotiation.

**Command syntax: mode [lacp-mode]**

**Command mode:** config

**Hierarchies**

- protocols lacp interface

**Note**
-	For LACP to operate, you must not set the interfaces on both sides of the link to passive mode.

-	At least one side must be active for the LACP negotiations to be initiated.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+-------------+---------+
| Parameter | Description                                                                      | Range       | Default |
+===========+==================================================================================+=============+=========+
| lacp-mode | ACTIVE is to initiate the transmission of LACP packets. PASSIVE is to wait for   | | active    | active  |
|           | peer to initiate the transmission of LACP packets. ACTIVE mode by default        | | passive   |         |
+-----------+----------------------------------------------------------------------------------+-------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# lacp
    dnRouter(cfg-protocols-lacp)# interface bundle-2
    dnRouter(cfg-protocols-lacp-if)# mode active

    dnRouter(cfg-protocols-lacp)# interface bundle-1
    dnRouter(cfg-protocols-lacp-if)# mode passive


**Removing Configuration**

To revert to the default mode:
::

    dnRouter(cfg-protocols-lacp-if)# no mode

**Command History**

+---------+-----------------------------------------------------+
| Release | Modification                                        |
+=========+=====================================================+
| 6.0     | Command introduced                                  |
+---------+-----------------------------------------------------+
| 10.0    | Static mode not supported, moved to a new hierarchy |
+---------+-----------------------------------------------------+
