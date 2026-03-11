segment-routing mpls color-map
------------------------------

**Command syntax: color-map [color-name] [color-value**

**Description:** Configure mapping of the color numeric value to humanly friendly alphanumeric name.
Color is a numerical value that distinguishes between two or more sr-policies to the same node pairs (Head-end – End point)
Operator may define color to reflect unique expected behavior from the sr policy, such as minimum latancy or high tolerance

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# segment-routing
	dnRouter(cfg-protocols-sr)# mpls
	dnRouter(cfg-protocols-sr-mpls)# color-map GREEN 2
	dnRouter(cfg-protocols-sr-mpls)# color-map RED 3


	dnRouter(cfg-protocols-sr-mpls)# no color-map GREEN
	dnRouter(cfg-protocols-sr-mpls)# no color-map

**Command mode:** config

**TACACS role:** operator

**Note:**

- Mapping is unique by name and value. I.e both name and value can only appear once in the mapping config

- The string "uncolored" will be kept for internal use only to mark sr-te policy without color for cases no color consideration should be applied when forwarding traffic over policy. User will not be able to configure color-name = "uncolored", the following error is expected upon commit "Error: Illigal color name in segment-routing mpls color-map, 'uncolored' is a special purpose reserved name"

- 'no color-map <color-name>' removes a specific color mapping

- 'no color-map' removes all color mapping

**Help line:** Map a user defined color name to a color value

**Parameter table:**

+-------------+---------------+---------------------+
| Parameter   | Values        | default value       |
+=============+===============+=====================+
| color-name  | string        |                     |
|             | length 1..64  |                     |
+-------------+---------------+---------------------+
| color-value | 0..4294967295 |                     |
+-------------+---------------+---------------------+