qos wred-profile 
-----------------

**Command syntax: wred-profile [profile-name] curve [curve-id] min [min-value] max [max-value]**

**Description:** configure wred curves

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# qos
	dnRouter(cfg-qos)# wred-profile my_profile
	dnRouter(cfg-qos-wred-profile-my_profile)# curve 0 min 500 max 1000
	dnRouter(cfg-qos-wred-profile-my_profile)# curve 1 min 100 max 1000
	
	dnRouter(cfg-qos)# wred-profile my_profile2
	dnRouter(cfg-qos-wred-profile-my_profile2)# curve 0 min 10 max 100
	
	dnRouter(cfg-qos)# no wred-profile 
	
	dnRouter(cfg-qos)# no wred-profile my_profile
	
	dnRouter(cfg-qos-wred-profile-default)# no curve 0
	
**Command mode:** config

**TACACS role:** operator

**Note:**

No qos wred-profile removes the whole wred-profile configuration.

Validation:

-  min value is less-or-equal to max value

-  User cannot remove or change global wred-profile as long is it attached to queue

**Help line:** Configure wred curves per forwarding class

**Parameter table:**

+--------------+-----------------------+---------------+
| Parameter    | Values                | Default value |
+==============+=======================+===============+
| Profile-name | string                |               |
+--------------+-----------------------+---------------+
| Curve-id     | 0 \|                  |               |
|              |                       |               |
|              | 1                     |               |
+--------------+-----------------------+---------------+
| Min          | 1-200 (milliseconds)  |               |
+--------------+-----------------------+---------------+
| Max          | 1-200 (milliseconds)  |               |
+--------------+-----------------------+---------------+
