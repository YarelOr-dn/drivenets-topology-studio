show flowspec-local-policies match-classes
------------------------------------------

**Minimum user role:** viewer

A FlowSpec Local rule is imposed on the entire system, specifically, on all interfaces that are FlowSpec enabled (see interfaces flowspec).
The show flowspec-local-policies match-classes command displays all the match-classes defined for each of the address families: ipv4/ipv6.
If the optional match-class-id parameter is given then the specific match-class with that name shall be displayed.
If the optional address-family parameter is given then the command displayes only the match-classes of the specified address-family.

**Command syntax: show flowspec-local-policies match-classes** {match-class match-class-id] \| address-family [ipv4/ipv6]}

**Command mode:** operational


**Parameter table**

+----------------+-----------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+
| Parameter      | Description                                                                                                                                         | Range             |
+================+=====================================================================================================================================================+===================+
| match-class-id | The match-class name. Filters the display to a specific match-class. Note the same match-class name may be present in each of the address families. | 0..255 characters |
+----------------+-----------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+
| ipv4 / ipv6    | Filters the display to a specific address family.                                                                                                   | ipv4 / ipv6       |
+----------------+-----------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+

For each Match Class, the following information is displayed:

+----------------+-----------------------------------------------------------------------------------------------------------+--------------------------+
| Parameter      | Description                                                                                               | Range                    |
+================+===========================================================================================================+==========================+
| Address-family | The address-family                                                                                        | IPv4                     |
|                |                                                                                                           | IPv6                     |
+----------------+-----------------------------------------------------------------------------------------------------------+--------------------------+
| Match Class Id | The Match Class Name and its description.                                                                 | \-                       |
+----------------+-----------------------------------------------------------------------------------------------------------+--------------------------+
| Match Class    | The Match Class NLRI information                                                                          | \-                       |
+----------------+-----------------------------------------------------------------------------------------------------------+--------------------------+

**Example**
::

	dnRouter# show flowspec-local-policies match-classes

Address-family: IPv4
        MC-1: Description: This is match-class-1
              DstPrefix:=50.0.0.0/8,SrcPrefix:=50.1.2.3/32,Protocol:=6,DstPort:12,SrcPort:50,Dscp:=5
        MC-2: Description: This is match-class-2
              DstPrefix:=52.0.0.0/8,SrcPrefix:=51.1.2.3/32,Protocol:=17,DstPort:3784
        MC-3: Description: This is match-class-3
              DstPrefix:=52.0.0.0/8,SrcPrefix:=51.1.2.3/32,Protocol:=17,DstPort:3784

Address-family: IPv6
        MC-4: Description Description: This is match-class-4
              DstPrefix:=2011:11:100:1::/64,SrcPrefix:=1500:1550:5::1/128,Protocol:=6,DstPort:6,SrcPort:=50,Dscp:=5



.. **Help line:** show flowspec-local-policies match-classes [match-class match-class-id] [address-family ipv4/ipv6]

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
