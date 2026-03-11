segment-routing mpls path segment-list weight
---------------------------------------------

**Command syntax: weight [weight]**

**Description:** Configure the weight of a given segment-list. The weight ratio between segment-lists of the same path will define the weighted traffic forwarding load balancing required between the different segment-lists.

For example if 2 segment-lists are configured for a given path, one with weight 1 and the other with weight 2. For a given tunnel using that path , traffic forwarded over that tunnel will be ditributed with 1:2 ratio between the 2 paths

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# segment-routing
	dnRouter(cfg-protocols-sr)# mpls
	dnRouter(cfg-protocols-sr-mpls)# path PATH_1
	dnRouter(cfg-sr-mpls-path)# segment-list 1
	dnRouter(cfg-mpls-path-sl)# weight 2

	dnRouter(cfg-mpls-path-sl)# no weight



**Command mode:** config

**TACACS role:** operator

**Note:**

- no command returns weight to default value

**Help line:** Configure the weight of a given segment-list

**Parameter table:**

+-------------+---------------+---------------------+
| Parameter   | Values        | default value       |
+=============+===============+=====================+
| weight      | 1..255        | 1                   |
+-------------+---------------+---------------------+

