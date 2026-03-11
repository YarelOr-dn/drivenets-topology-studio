protocols segment-routing mpls policy destination
-------------------------------------------------

**Minimum user role:** operator

The destination is the last hop (tail-end) of the segment-routing policy and is a mandatory configuration.
The configuration is much like the hop configuration (see "segment-routing mpls path segment-list hop"), except that it marks the last hop.

To configure the policy's destination:


**Command syntax: destination [destination ip-address] [destination-algorithm]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls policy

**Note**
- There's no remove option for the destination as it is a mandatory config for the policy. The user can change the assigned destination.


**Parameter table**

+------------------------+----------------------------------------------+----------------+---------+
| Parameter              | Description                                  | Range          | Default |
+========================+==============================================+================+=========+
| destination ip-address | segment-routing policy destination           | | A.B.C.D      | \-      |
|                        |                                              | | X:X::X:X     |         |
+------------------------+----------------------------------------------+----------------+---------+
| destination-algorithm  | segment-routing policy destination algorithm | | spf          | \-      |
|                        |                                              | | strict-spf   |         |
+------------------------+----------------------------------------------+----------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protcols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# policy SR_POLICY_1
    dnRouter(cfg-sr-mpls-policy)# destination 1.1.1.1 strict-spf

    dnRouter# configure
    dnRouter(cfg)# protcols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# policy SR_v6_POLICY_1
    dnRouter(cfg-sr-mpls-policy)# destination 1717:1717::1 strict-spf


**Removing Configuration**

To remove a destination:
::

    The destination is mandatory. You can only change it, not remove it.

**Command History**

+---------+----------------------------------+
| Release | Modification                     |
+=========+==================================+
| 15.0    | Command introduced               |
+---------+----------------------------------+
| 18.2    | Add support for ipv6 destination |
+---------+----------------------------------+
