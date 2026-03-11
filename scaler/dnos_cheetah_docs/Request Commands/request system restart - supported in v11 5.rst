request system restart - supported in v11.5
-------------------------------------------

**Minimum user role:** admin

request system restart operation

-  By default, preform cold restart, meaning power reset for all elements in the cluster.

-  specify node type and id to restart specific node in cluster

-  warm - restart DNOS software (applicative containers) only.

**Command syntax: request system process stop {ncc [ncc-id] \| ncp [ncp-id] \| ncf [ncf-id]} [container-name] [process-name]**
		
**Command mode:** operational

**Note:**

-  Yes/no validation should exist for system restart operation.

-  Request system restart warm performs applicative containers restart across all the system.

   -  Applicative containers are Management-engine, Routing-engine, Forwarding-engine and selector.

-  In order to cold restart the standby NCC, there must be connectivity for standby NCC

-  For "request system restart warm" NCM will not reset. Cannot choose warm restart for node type of ncm

*Parameter table:**

+-----------+----------------+---------------+
| Parameter | Values         | Default value |
+===========+================+===============+
| ncc-id    | 0-1            |               |
+-----------+----------------+---------------+
| ncp       | 0-249          |               |
+-----------+----------------+---------------+
| ncf       | 0-611          |               |
+-----------+----------------+---------------+
| ncm-id    | a0, b0, a1, b1 |               |
+-----------+----------------+---------------+


**Example**
::

	dnRouter# request system restart
	Warning: Are you sure you want to perform a system restart? (Yes/No) [No]? 
	
	dnRouter# request system restart warm
	Warning: Are you sure you want to perform a system restart? (Yes/No) [No]? 
	
	dnRouter# request system restart ncc 1
	Warning: Are you sure you want to perform a system restart? (Yes/No) [No]? 
	
	dnRouter# request system restart ncp 3 warm
	Warning: Are you sure you want to perform a system restart? (Yes/No) [No]? 
	
	dnRouter# request system restart ncm a1
	Warning: Are you sure you want to perform a system restart? (Yes/No) [No]? 
	
		
