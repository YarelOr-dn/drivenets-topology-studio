qos traffic-class-map 802.1p 
-----------------------------

**Command syntax: 802.1p [802.1p-value]** [,802.1p-value, 802.1p-value .]

**Description:** Configure the traffic-class map to classify based on 802.1p. Matching available if sub-interfaces policies are attached.

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# qos
	dnRouter(cfg-qos)# traffic-class-map MyTrafficMap1 
	dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# 802.1p 4 
	
	dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# 802.1p 5,6,7
	
	dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# no 802.1p
	
	dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# no 802.1p 5,6
	
	
**Command mode:** config qos traffic-class-map

**TACACS role:** operator

**Note:** 'no 802.1p\` command removes the 802.1p configuration. 'no 802.1p' can remove set of values

**Help line:** 802.1p value

**Parameter table:**

+---------------+------------------------------------+---------------+
| Parameter     | Values                             | Default value |
+===============+====================================+===============+
| 802.1p -value | 0-7                                |               |
|               |                                    |               |
|               | up to 8 values, separated by comma |               |
+---------------+------------------------------------+---------------+
