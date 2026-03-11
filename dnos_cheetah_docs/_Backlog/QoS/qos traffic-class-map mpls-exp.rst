qos traffic-class-map mpls-exp 
-------------------------------

**Command syntax: mpls-exp [exp-value]** [,exp-value, exp-value.]

**Description:** Configure the traffic-class map to classify based on MPLS experimental bits

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# qos
	dnRouter(cfg-qos)# traffc-class-map MyTrafficMap1 
	dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# mpls-exp 1,3,5 
	
	dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# no mpls-exp 1,3
	
	dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# no mpls-exp
	
	
**Command mode:** config qos traffic-class-map

**TACACS role:** operator

**Note:** when match type of the traffic-class map is match-all, only one value of mpls exp is allowed.

'no mpls-exp' command remove the mpls exp configuration. 'no mpls-exp' can remove set of values

**Help line:** mpls experimental value

**Parameter table:**

+-----------+------------------------------------+---------------+
| Parameter | Values                             | Default value |
+===========+====================================+===============+
| exp-value | 0-7                                |               |
|           |                                    |               |
|           | up to 8 values, separated by comma |               |
+-----------+------------------------------------+---------------+
