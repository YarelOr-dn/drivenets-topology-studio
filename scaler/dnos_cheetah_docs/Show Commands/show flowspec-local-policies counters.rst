show flowspec-local-policies counters
-------------------------------------

**Minimum user role:** viewer

The Show flowspec-local-policy counters command displays for each of the address families, the installed policy and the associated counter information,
that is, the number of matches to each of the match-classes in the installed policy.
If the optional address-family parameter is given then the command displayes only the policies of the specified address-family.

**Command syntax: show flowspec-local-policies counters** {address-family [ipv4/ipv6]}

**Command mode:** operational


**Parameter table**

+-----------+-----------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+
| Parameter | Description                                                                                                                                         | Range             |
+===========+=====================================================================================================================================================+===================+
| ipv4 /    | Filters the display to a specific address family.                                                                                                   | ipv4 / ipv6       |
| ipv6      |                                                                                                                                                     |                   |
+-----------+-----------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+




For each Address Family, ipv4/ipv6, the installed Flowspec-Local Policy is displayed with the following information:

+----------------+-----------------------------------------------------------------------------------------------------------+--------------------------+
| Parameter      | Description                                                                                               | Range                    |
+================+===========================================================================================================+==========================+
| Address-family | The address-family                                                                                        | IPv4                     |
|                |                                                                                                           | IPv6                     |
+----------------+-----------------------------------------------------------------------------------------------------------+--------------------------+
| Policy Id      | The Policy Name and its description.                                                                      | \-                       |
+----------------+-----------------------------------------------------------------------------------------------------------+--------------------------+
| Match Class    | For eaxch of the policies Match-Classes, the Match Class Name and its NLRI information                    | \-                       |
+----------------+-----------------------------------------------------------------------------------------------------------+--------------------------+
| Actions        | The action(s) to take on the flow                                                                         | Rate-Limit: 0 (= drop)   |
|                |                                                                                                           | Redirect-to-vrf.         |
|                |                                                                                                           | Else, allow              |
+----------------+-----------------------------------------------------------------------------------------------------------+--------------------------+

**Example**
::

	dnRouter# show flowspec-local-policies counters

    Address-family: IPv4
      Policy-2: Description: Rate limits UDP traffic from source-S intended for destination-D
         MC-2: Decsription: match-class-2
               DstPrefix:=52.0.0.0/8,SrcPrefix:=51.1.2.3/32,Protocol:=17,DstPort:3784
            Actions: Rate-Limit: 10000000 bps
            Match packets: 1000
          MC-3: Decsription: match-class-3
               DstPrefix:=10.10.10.0/24,SrcPrefix:=51.1.2.3/32,Protocol:=17,DstPort:3784
            Actions: Redirect-to-vrf: vrf-1
            Match packets: 2


    Address-family: IPv6
        Policy-3: Redirects and Rate Limits TCP traffic with source port either 30 or 50
          MC-4: Decsription: match-class-4
                DstPrefix:=2011:11:100:1::/64,SrcPrefix:=1500:1550:5::1/128,Protocol:=6,DstPort:12,SrcPort:=50,Dscp:=5
            Actions: Redirect-to-vrf: vrf-6, Rate-Limit: 5000000 bps
            Match packets: 5156

.. **Help line:** show flowspec-local-policies counters [address-family ipv4/ipv6]

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
