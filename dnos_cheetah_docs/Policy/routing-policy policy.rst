routing-policy policy
---------------------

**Minimum user role:** operator

Policies provide a means to filter and/or apply actions to a route, thus allowing policies to be applied to routes. The policy includes an ordered list of entries, where each entry may specify the following: 

-	Matching conditions: the conditions which must be matched if the entry is to be considered further. If no conditions are defined, then the entry is always met. If more than one condition is defined, all conditions must be met.

-	Set Actions: a policy entry may optionally specify one or more actions to set or modify attributes of the route. If multiple actions are defined, all actions are performed (if the proper conditions are met).

To create a policy and enter its configuration mode:


**Command syntax: policy [policy-name]**

**Command mode:** config

**Hierarchies**

- routing-policy

**Note**

- You cannot delete a policy that is attached to a BGP or OSPF process.

..
	**Internal Note**

	-  validation:

	   | if a user tries to remove a policy while it is attached to a {BGP,OSPF} process, the following error should be displayed:
	   
	   | "Error: unable to remove policy <policy-name>. policy is attached to BGP<router-id>".

**Parameter table**

+----------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------+-------------+
|                |                                                                                                                                                             |           |             |
| Parameter      | Description                                                                                                                                                 | Range     | Default     |
+================+=============================================================================================================================================================+===========+=============+
|                |                                                                                                                                                             |           |             |
| policy-name    |  Provide a   name for the policy. Names with spaces must be enclosed in quotation marks.   If you do not want to use quotation marks, do not use spaces.    | 1..255    | \-          |
+----------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy SET_FULL_ROUTES
	dnRouter(cfg-rpl-policy)#
	
	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy MY_POL
	dnRouter(cfg-rpl-policy)#


**Removing Configuration**

To remove the policy:
::

	dnRouter(cfg-rpl)# no policy SET_FULL_ROUTES
	dnRouter(cfg-rpl)# no policy MY_POL

.. **Help line:** Create route distribute policy

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 6.0         | Command introduced    |
+-------------+-----------------------+