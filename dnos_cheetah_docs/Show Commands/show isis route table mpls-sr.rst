show isis route table mpls-sr
-----------------------------

**Minimum user role:** viewer

To display IS-IS routing information of segment-routing and Flex-Algo:



**Command syntax: show isis** instance [isis-instance-name] **route** [mpls-label] **table mpls-sr** algorithm [algorithm]

**Command mode:** operational


..
	**Internal Note**

	- use "instance [isis-instance-name]" to display information from a specific ISIS instance, when now specified, display information from all isis instances
	- nexthop-srgb-base represent the nexthop expected to handle the route level label. For ISIS-SR routes it means the nexthop which will get the SR prefix-sid label. In case of ti-lfa/uloop-avoidance usage, it may be a remote Q node

**Parameter table**

+--------------------+--------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------+
| Parameter          | Description                                                                                                                    | Range                                           |
+====================+================================================================================================================================+=================================================+
| isis-instance-name | Displays routes for a specific IS-IS instance. If you do not specify an instance, routes from all instances will be displayed  | 1..255 characters                               |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------+
| mpls-label         | Filters the displayed routes to routes matching the specified mpls-label                                                       | <16-1048575>                                    |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------+
| table mpls-sr      | Displays ISIS-SR ILM routes of both SR and Flex-algo                                                                           | \-                                              |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------+
| algorithm          | Filter routes that are from a given Flex-Algo id                                                                               | <128-255>                                       |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------+


**Example**
::

	dnRouter# show isis route 16003 table mpls-sr

	Legend: lp - link-protecting LFA, np - node-protecting LFA, L - ldp-stitching, ul - microloop-avoidance
	Instance one
	ipv4 segment-routing mpls table:
	Level - 2
	Destination         Prefix              algorithm    cost    tag           priority         nh-address                 interface            egress-label   Nexthop-srgb-base
	16003               2.2.2.2/32          spf          10      Untagged      Medium           10.0.13.3                  ge100-0/0/3              3              16000

	dnRouter# show isis route table mpls-sr algorithm 130

	Legend: lp - link-protecting LFA, np - node-protecting LFA, L - ldp-stitching, ul - microloop-avoidance
	Instance one
	ipv4 segment-routing mpls table:
	Level - 1

	Instance one
	ipv4 segment-routing mpls table:
	Level - 2
	Destination         Prefix              algorithm    cost    tag           priority         nh-address                 interface            egress-label   Nexthop-srgb-base
	17302               2.2.2.2/32          130          10      Untagged      Medium           10.0.12.2                  ge100-0/0/2              3              16000
	17303               3.3.3.3/32          130          10      Untagged      Medium           10.0.13.3                  ge100-0/0/3              3              16000
	17304               4.4.4.4/32          130          20      Untagged      Medium           10.0.12.2                  ge100-0/0/2              17304          16000
	                                                     20      Untagged      Medium           10.0.13.3                  ge100-0/0/3              17304          16000
	17305               100.50.50.50/32     130          20      Untagged      Medium           10.0.13.3                  ge100-0/0/3              17305          16000
	17306               100.60.60.60/32     130          10      Untagged      Medium           10.0.16.6                  ge100-0/0/6              3              16000
	17307               100.70.70.70/32     130          30      Untagged      Medium           10.0.12.2                  ge100-0/0/2              17307          16000
	                                                     30      Untagged      Medium           10.0.13.3                  ge100-0/0/3              17307          16000
	17308               100.11.11.11/32     130          30      Untagged      Medium           10.0.13.3                  ge100-0/0/3              17308          16000


**Command History**

+---------+---------------------------------------------+
| Release | Modification                                |
+=========+=============================================+
| 18.0    | Added Flex-Algo features                    |
+---------+---------------------------------------------+
