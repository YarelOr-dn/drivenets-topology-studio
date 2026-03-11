routing-options
---------------

**Minimum user role:** operator

The routing options configuration hierarchy allows you to filter out routes that are installed in the routing tables based on policies. This is done per routing table. To apply a policy to the routing table follow this general procedure:

Enter the routing-options configuration hierarchy (see below).
Enter the configuration hierarchy for the specific routing table. See routing-options table.
Select the policy to apply to the table. See routing-options table install-policy.
To enter the routing options configuration mode:

**Command syntax: routing-options**

**Command mode:** config

**Note**

- Notice the change in prompt.

.. - no command returns all routing-options configurations to their default state

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-options
	dnRouter(cfg-routing-option)# 
	
	
	

**Removing Configuration**

To revert all routing-options configurations to their default state:
::

	dnRouter(cfg)# no routing-options

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+


