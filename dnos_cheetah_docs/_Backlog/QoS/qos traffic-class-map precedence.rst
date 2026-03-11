qos traffic-class-map precedence 
---------------------------------

**Command syntax: precedence [precedence-value]** [,precedence-value, precedence-value.]

**Description:** Configure the traffic-class-map to classify based on ip precedence. User can configure either precedence or dscp in traffic-class-map. Precedence value relates to ipv4 and ipv6 address family.

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# qos
	dnRouter(cfg-qos)# traffic-class-map MyTrafficMap1 
	dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# precedence 1,3,5 
	
	dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# no precedence
	
	dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# no precedence 1
	
	
**Command mode:** config qos traffic-class-map

**TACACS role:** operator

**Note:** when match type of the traffic-class map is match-all, only one value of ip precedence is allowed.

'no precedence' command remove the precedence configuration. 'no precedence' can remove set of values.

**Help line:** precedence value

**Parameter table:**

+------------------+-----------------------------------------------+---------------+
| Parameter        | Values                                        | Default value |
+==================+===============================================+===============+
| Precedence-value | 0-7                                           |               |
|                  |                                               |               |
|                  | Up to 8 precedence values, separated by comma |               |
+------------------+-----------------------------------------------+---------------+
