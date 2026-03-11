qos traffic-class-map qos-tag 
------------------------------

**Command syntax: qos-tag [qos-tag-value]** [,qos-tag-value, qos-tag-value .]

**Description:** Configure the traffic-class map to classify based on qos-tag. The qos-tag is internal header that can be set on ingress policy and used on egress policy

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# qos
	dnRouter(cfg-qos)# traffic-class-map MyTrafficMap1 
	dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# qos-tag 4 
	
	
	dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# qos-tag 5,6,7 
	
	dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# no qos-tag
	
	dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# no qos-tag 6,7
	
	
**Command mode:** config qos traffic-class-map

**TACACS role:** operator

**Note:** 'no qos-tag\` command removes the qos-tag configuration. 'no qos-tag' can remove set of values

**Help line:** qos-tag value

**Parameter table:**

+---------------+------------------------------------+---------------+
| Parameter     | Values                             | Default value |
+===============+====================================+===============+
| qos-tag-value | 0-7                                |               |
|               |                                    |               |
|               | up to 8 values, separated by comma |               |
+---------------+------------------------------------+---------------+
