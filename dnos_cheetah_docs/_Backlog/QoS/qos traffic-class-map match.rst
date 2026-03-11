qos traffic-class-map match
---------------------------

**Command syntax: match** [match-type]

**Description:** Configure the traffic-class map match type.

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# qos
	dnRouter(cfg-qos)# traffic-class-map MyTrafficMap1 
	dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# match any 
	dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# no match
	
	
**Command mode:** config qos traffic-class-map

**TACACS role:** operator

**Note:**

Match-type is defined only in creation of the traffic-class-map. It can't be modified after the traffic-class-map is created.

**Help line:** dscp value

**Parameter table:**

+------------+---------------------+---------------+--------------------------------------------------------------------------------+
| Parameter  | Values              | Default value | comment                                                                        |
+============+=====================+===============+================================================================================+
| match-type | Any                 | any           | Match-type is set only when traffic-class-map is created. It can't be modified |
|            |                     |               |                                                                                |
|            | All (not supported) |               | In order to modify, the traffic-class-map should be deleted and re-created.    |
+------------+---------------------+---------------+--------------------------------------------------------------------------------+
