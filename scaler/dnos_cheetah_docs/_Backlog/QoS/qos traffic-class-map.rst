qos traffic-class-map 
----------------------

**Command syntax: traffic-class-map [traffic-class-map-name]**

**Description:** configure a qos traffic-class-map

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# qos
	dnRouter(cfg-qos)# traffic-class-map myTrafficMap1 
	dnRouter(cfg-qos)# no traffic-class-map myTrafficMap1 
	
**Command mode:** config

**TACACS role:** operator

**Note:**

no command remove the traffic-class-map configuration

Validation: a traffic-class-map cannot be deleted if it is used in a policy. The following warning will be printed

"Error: cannot delete traffic-class-map <traffic-class-map_name>. traffic-class-map is used in a policy"

**Help line:** Configure qos traffic-class-map

**Parameter table:**

+------------------------+--------+---------------+
| Parameter              | Values | Default value |
+========================+========+===============+
| Traffic-class-map-name | String |               |
+------------------------+--------+---------------+
