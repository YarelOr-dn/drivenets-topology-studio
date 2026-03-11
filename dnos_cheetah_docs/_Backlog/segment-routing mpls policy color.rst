segment-routing mpls policy color
---------------------------------

**Command syntax: color [color-name]**

**Description:** Configure the SR policy color.

Color is a numerical value that distinguishes between two or more sr-policies to the same node pairs (Head-end – End point)
Operator may define color to reflect unique expected behavior from the sr policy, such as minimum latancy or high tolerance

Color 0 has unique meaning in DNOS system. Policies defined with color 0 will be handled as "uncolored" SR-TE policies.
For example, if FTN installation is required to the mpls-nh table, policy will be installed there, and no color consideration should be applied when forwarding traffic over the sr-te policy.


**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# segment-routing
	dnRouter(cfg-protocols-sr)# mpls
	dnRouter(cfg-protocols-sr-mpls)# policy POL_1
	dnRouter(cfg-sr-mpls-policy)# color 20

	dnRouter(cfg-sr-mpls-policy)# no color



**Command mode:** config

**TACACS role:** operator

**Note:**

- Commit validation: There can't be more than one policy to a given destination with the same color , including default 0 ("uncolored")

- no commend return color to default value

**Help line:** Configure sr policy color

**Parameter table:**

+-------------+------------------------+----------------+
| Parameter   | Values                 | default value  |
+=============+========================+================+
| color       | 0..4294967295          | 0              |
+-------------+------------------------+----------------+
