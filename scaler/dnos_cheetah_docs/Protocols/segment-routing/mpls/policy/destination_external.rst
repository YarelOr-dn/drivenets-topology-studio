protocols segment-routing mpls policy destination external
----------------------------------------------------------

**Minimum user role:** operator

The destination is the last hop (tail-end) of the segment-routing policy and is a mandatory configuration.
Configure the policy destination as an external SID to the SR-TE policy label stack. The policy label stack will fully be defined by the provided path.
To configure the policy's destination as external:


**Command syntax: destination [destination ip-address] external**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls policy

**Parameter table**

+------------------------+------------------------------------+--------------+---------+
| Parameter              | Description                        | Range        | Default |
+========================+====================================+==============+=========+
| destination ip-address | segment-routing policy destination | | A.B.C.D    | \-      |
|                        |                                    | | X:X::X:X   |         |
+------------------------+------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# policy SR-POLICY_1
    dnRouter(cfg-sr-mpls-policy)# destination 1.1.1.1 external

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# policy SR-_v6_POLICY_1
    dnRouter(cfg-sr-mpls-policy)# destination 1717:1717::1 external


**Removing Configuration**

To remove destination configuration:
::

    dnRouter(cfg-sr-mpls-policy)# no destination

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
