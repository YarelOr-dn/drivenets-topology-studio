show flowspec-local-policies policies
-------------------------------------

**Minimum user role:** viewer

A FlowSpec Local rule is imposed on the entire system, specifically, on all interfaces that are FlowSpec enabled (see interfaces flowspec).
The show flowspec-local-policies policies command displays all the policies defined for each of the address families: ipv4/ipv6.
If the optional policy-name parameter is given then the specific policy(s) with that name shall be displayed.
If the optional address-family parameter is given then the command displayes only the policies of the specified address-family.
For each policy defined, the match-classes and the match-class actions are displayed.

**Command syntax: show flowspec-local-policies policies** {policy [policy-id] \| address-family [ipv4/ipv6]}

**Command mode:** operational


**Parameter table**

+-----------+-----------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+
| Parameter | Description                                                                                                                                         | Range             |
+===========+=====================================================================================================================================================+===================+
| policy-id | The policy name. Filters the display to a specific policy. Note the same policy name may be present in each of the address families.                | 0..255 characters |
+-----------+-----------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+
| ipv4 /    | Filters the display to a specific address family.                                                                                                   | ipv4 / ipv6       |
| ipv6      |                                                                                                                                                     |                   |
+-----------+-----------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+

For each Policy, the following information is displayed:

+----------------+-----------------------------------------------------------------------------------------------------------+--------------------------+
| Parameter      | Description                                                                                               | Range                    |
+================+===========================================================================================================+==========================+
| Address-family | The address-family                                                                                        | IPv4                     |
|                |                                                                                                           | IPv6                     |
+----------------+-----------------------------------------------------------------------------------------------------------+--------------------------+
| Policy Id      | The Policy Name and its description.                                                                      | \-                       |
+----------------+-----------------------------------------------------------------------------------------------------------+--------------------------+
| Match Class    | The Match Class Name and its NLRI information                                                             | \-                       |
+----------------+-----------------------------------------------------------------------------------------------------------+--------------------------+
| Actions        | The action to take on the flow                                                                            | Traffic-rate: 0 (= drop) |
|                |                                                                                                           | Redirect-to-vrf.         |
|                |                                                                                                           | Else, allow              |
+----------------+-----------------------------------------------------------------------------------------------------------+--------------------------+

**Example**
::

	dnRouter# show flowspec-local-policies policies

    Address-family: IPv4
      Policy-1: Description: Rate limits TCP traffic from source-S intended for destination-D
          MC-2: Decsription: match-class-2
               DstPrefix:=52.0.0.0/8,SrcPrefix:=51.1.2.3/32,Protocol:=6,DstPort:4134
            Actions: Traffic-rate: 1000000 bps

          MC-3: Decsription: match-class-3
               DstPrefix:=10.10.10.0/24,SrcPrefix:=51.1.2.3/32,Protocol:=6,DstPort:4134
            Actions: Redirect: 1.2.3.4


      Policy-2: Description: Rate limits UDP traffic from source-S intended for destination-D
         MC4: Decsription: match-class-2
               DstPrefix:=52.0.0.0/8,SrcPrefix:=51.1.2.3/32,Protocol:=17,DstPort:3784
            Actions: Traffic-rate: 5000000 bps

          MC-5: Decsription: match-class-3
               DstPrefix:=10.10.10.0/24,SrcPrefix:=51.1.2.3/32,Protocol:=17,DstPort:3784
            Actions: Redirect: 1.1.1.1


.. **Help line:** show flowspec-local-policies policies [policy policy-id] [address-family ipv4/ipv6]

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
