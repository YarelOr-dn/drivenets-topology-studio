access-lists log-interval - supported in v12
--------------------------------------------

**Command syntax: log-interval [interval]**

**Description:** configure access-lists global log-interval

Log interval specifies the interval in which to write a log entry for the matched packets to a dedicated log file.

This configuration sets the default interval for all access-lists configured on the device. The interval is defined as number of packets that must be matched by ACL policy rules before a ACL match log is generated. The first matched by the one of ACL rules will generate a log entry. The next time the matched packet will generate a log will be only after number of matched packets by the ACL rules will exceed the configured interval.

The following parameters are logged per matched packet:

-  interface

-  attachment direction

-  acl policy name

-  acl type

-  matched rule-id

-  action

-  matched packet 5-tuple

-  match counter

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# access-lists 
	dnRouter(cfg-acl)# log-interval 20
	
	dnRouter(cfg-acl)# no log-interval
	
**Command mode:** config

**TACACS role:** operator

**Note:**

no commands revert the access-lists log-interval to its default value

**Help line:** Configure access-lists log-interval

**Parameter table:**

+-----------+----------------+---------------+
| Parameter | Values         | Default value |
+===========+================+===============+
| interval  | 5-2000 packets | 300 packets   |
+-----------+----------------+---------------+
