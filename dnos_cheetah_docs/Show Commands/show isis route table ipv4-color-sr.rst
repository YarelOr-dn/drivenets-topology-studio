show isis route table ipv4-color-sr
-----------------------------------

**Minimum user role:** viewer

To display IS-IS routing information for Flex-Algo:



**Command syntax: show isis** instance [isis-instance-name] **route** [prefix] **table ipv4-color-sr** algorithm [algorithm] color [color]

**Command mode:** operational


..
	**Internal Note**

	- use "instance [isis-instance-name]" to display information from a specific ISIS instance, when now specified, display information from all isis instances
	- nexthop-srgb-base represent the nexthop expected to handle the route level label. For ISIS-SR routes it means the nexthop which will get the SR prefix-sid label. In case of ti-lfa/uloop-avoidance usage, it may be a remote Q node

**Parameter table**

+---------------------+--------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------+
| Parameter           | Description                                                                                                                    | Range                                           |
+=====================+================================================================================================================================+=================================================+
| isis-instance-name  | Displays routes for a specific IS-IS instance. If you do not specify an instance, routes from all instances will be displayed  | 1..255 characters                               |
+---------------------+--------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------+
| prefix              | Filters the displayed routes to routes matching the specified prefix                                                           | A.B.C.D/M                                       |
+---------------------+--------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------+
| table ipv4-color-sr | Display ISIS-SR routes of specific Flex Algo                                                                                   | \-                                              |
+---------------------+--------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------+
| algorithm           | Filter routes that are from a given Flex-Algo id                                                                               | <128-255>                                       |
+---------------------+--------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------+
| color               | Filter routes that are for a given color                                                                                       | <0-4294967295>                                  |
+---------------------+--------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------+


**Example**
::


	dnRouter#  show isis route table ipv4-color-sr color 30
	Legend: lp - link-protecting LFA, np - node-protecting LFA, L - ldp-stitching, ul - microloop-avoidance
	Instance one
	ipv4 segment-routing mpls table:
	Level - 1


	Instance one
	ipv4 segment-routing mpls table:
	Level - 2
	Destination         algorithm    cost    tag           priority         nh-address                 interface            egress-label   Nexthop-srgb-base
	30:2.2.2.2/32       130          10      Untagged      Low              10.0.12.2                  ge100-0/0/2              3              16000
	30:3.3.3.3/32       130          20      Untagged      Low              10.0.12.2                  ge100-0/0/2              17303          16000
	30:4.4.4.4/32       130          20      Untagged      Low              10.0.12.2                  ge100-0/0/2              17304          16000
	30:5.5.5.5/32       130          30      Untagged      Low              10.0.12.2                  ge100-0/0/2              17305          16000
	30:6.6.6.6/32       130          10      Untagged      Low              10.0.16.6                  ge100-0/0/6              3              16000
	30:7.7.7.7/32       130          30      Untagged      Low              10.0.12.2                  ge100-0/0/2              17307          16000
	30:8.8.8.8/32       130          40      Untagged      Low              10.0.12.2                  ge100-0/0/2              17308          16000


**Command History**

+---------+---------------------------------------------+
| Release | Modification                                |
+=========+=============================================+
| 18.0    | Added Flex-Algo features                    |
+---------+---------------------------------------------+
