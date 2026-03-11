qos traffic-class-map dscp
--------------------------

**Command syntax: dscp [dscp-value]** [dscp-value , dscp-value.]

**Description:** Configure the traffic-class map to classify based on DSCP. User can configure either precedence or dscp in traffic-class-map. dscp value relates to ipv4 and ipv6 address family.

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# qos
	dnRouter(cfg-qos)# traffic-class-map MyTrafficMap1 
	dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# dscp 10,12,14 
	dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# no dscp 10,12
	dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# no dscp
	
	
**Command mode:** config qos traffic-class-map

**TACACS role:** operator

**Note:**

when match-type of the traffic-class map is match all, only one value of dscp is allowed.

'no dcsp' command remove the dscp configuration. 'no dscp' can remove set of values.

**Help line:** dscp value

**Parameter table:**

+------------+-------------------------------------+---------------+
| Parameter  | Values                              | Default value |
+============+=====================================+===============+
| Dscp-Value | 0-63                                |               |
|            |                                     |               |
|            | up to 64 values, separated by comma |               |
+------------+-------------------------------------+---------------+
