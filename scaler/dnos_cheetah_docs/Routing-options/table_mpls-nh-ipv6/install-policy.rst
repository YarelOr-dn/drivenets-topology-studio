routing-options table mpls-nh-ipv6 install-policy
-------------------------------------------------

**Minimum user role:** operator

To set the import policy to apply on routes being installed in the routing table:


**Command syntax: install-policy [install-policy]**

**Command mode:** config

**Hierarchies**

- routing-options table mpls-nh-ipv6

**Note**

- policy only support the following action: match ipv4|ipv6 prefix [prefix-list-name]

- policy rule apply regardless of originating protocol

**Parameter table**

+----------------+---------------------------------------------------------------------------+------------------+---------+
| Parameter      | Description                                                               | Range            | Default |
+================+===========================================================================+==================+=========+
| install-policy | Set import policy to apply on routes being installed in the routing table | | string         | \-      |
|                |                                                                           | | length 1-255   |         |
+----------------+---------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# table mpls-nh-ipv6
    dnRouter(cfg-routing-option-mpls-nh-ipv6)# install-policy MPLS_NH_IPv6_POL


**Removing Configuration**

To remove the import policy:
::

    dnRouter(cfg-routing-option-mpls-nh-ipv6)# no install-policy

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
