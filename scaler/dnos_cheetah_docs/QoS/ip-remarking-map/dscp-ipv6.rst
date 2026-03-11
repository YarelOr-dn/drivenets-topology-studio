qos ip-remarking-map qos-tag drop-tag dscp-ipv6
-----------------------------------------------

**Minimum user role:** operator

To configure an entry in the qos ip-remarking map:

**Command syntax: qos-tag [qos-tag] drop-tag [drop-tag] dscp-ipv6 [dscp-ipv6]** mpls-imposed-exp [mpls-imposed-exp]

**Command mode:** config

**Hierarchies**

- qos ip-remarking-map

**Parameter table**

+------------------+----------------------------------------------------+------------+---------+
| Parameter        | Description                                        | Range      | Default |
+==================+====================================================+============+=========+
| qos-tag          | qos-tag identifier.                                | 0-7        | \-      |
+------------------+----------------------------------------------------+------------+---------+
| drop-tag         | drop-tag identifier.                               | | green    | \-      |
|                  |                                                    | | yellow   |         |
+------------------+----------------------------------------------------+------------+---------+
| dscp-ipv6        | the dscp remark value for ipv6 address family.     | 0-63       | \-      |
+------------------+----------------------------------------------------+------------+---------+
| mpls-imposed-exp | the imposed mpls-exp carrying IP remarked traffic. | 0-7        | \-      |
+------------------+----------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# ip-remarking-map
    dnRouter(cfg-qos-ip-remark)#
    dnRouter(cfg-qos-ip-remark)# qos-tag 4 drop-tag green dscp-ipv6 af11
    dnRouter(cfg-qos-ip-remark)# qos-tag 4 drop-tag yellow dscp-ipv6 af12
    dnRouter(cfg-qos-ip-remark)# qos-tag 4 drop-tag yellow dscp-ipv6 af12 mpls-imposed-exp 3


**Removing Configuration**

To remove the qos ip-remarking-map entry:
::

    dnRouter(cfg-qos-ip-remark)# no qos-tag 4 drop-tag green

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
