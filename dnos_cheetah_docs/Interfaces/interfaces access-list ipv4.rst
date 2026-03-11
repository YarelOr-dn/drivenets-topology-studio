interfaces access-list ipv4 direction
-------------------------------------

**Minimum user role:** operator

After creating an access-list, you can link it to an interface. When applying an access-list to an interface, you must specify whether it is to be applied to inbound or outbound traffic. You can configure only one access-list per direction for each access-list type.

The attachment of the policy to the interface will be rejected.


To apply an access-list to an interface, use the following command:

**Command syntax: access-list ipv4 [access-list-name] direction [direction]**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to the following interface types:

  - Bundle
  - Bundle vlan
  - Physical
  - Physical vlan
  - mgmt0
  - IRB

**Parameter table**

+------------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter        | Description                                                                      | Range   | Default |
+==================+==================================================================================+=========+=========+
| access-list-name | Specify the name of an existing access-list. This access-list will serve as a    | \-      | \-      |
|                  | global access-list.                                                              |         |         |
+------------------+----------------------------------------------------------------------------------+---------+---------+
| direction        | The direction of the traffic to which to apply the access-list. For mgmt         | | in    | \-      |
|                  | interfaces, you can configure only an ingress access-list.                       | | out   |         |
+------------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# bundle-1
    dnRouter(cfg-if-bundle-1)# access-list ipv4 MyAccess-listv4 direction in

    dnRouter(cfg-if)# bundle-1.10
    dnRouter(cfg-if-bundle-1.10)# access-list ipv4 MyAccess-listv4 direction out

    dnRouter(cfg-if)# ge100-1/1/1
    dnRouter(cfg-if-ge100-1/1/1)# access-list ipv4 MyAccess-listv4 direction in

    dnRouter(cfg-if)# ge100-1/1/1.20
    dnRouter(cfg-if-ge100-1/1/1.20)# access-list ipv4 MyAccess-listv4 direction out

    dnRouter(cfg-if)# bundle-2
    dnRouter(cfg-if-bundle-2)# access-list ipv4 MyAccess-listv4 direction in


**Removing Configuration**

To remove all the access lists from the interface:
::

    dnRouter(cfg-if-ge100-1/1/1)# # no access-list

To remove all ipv4 access-lists from the interface:
::

    dnRouter(cfg-if-ge100-1.20)# no access-list ipv4

To remove a specific access-list from the interface:
::

    dnRouter(cfg-if-bundle-2)# no access-list ipv4 MyAccess-listv4

**Command History**

+---------+--------------------------------------------------------------------+
| Release | Modification                                                       |
+=========+====================================================================+
| 5.1     | Command introduced                                                 |
+---------+--------------------------------------------------------------------+
| 6.0     | Changed syntax from interface to interfaces; applied new hierarchy |
+---------+--------------------------------------------------------------------+
| 11.1    | Added direction out                                                |
+---------+--------------------------------------------------------------------+
