system aaa-server fallback-on-reject
------------------------------------

**Minimum user role:** admin

When enabled, allows automatic fallback to the secondary authentication method (if configured) also in the case of a rejected primary method attempt

**Command syntax: fallback-on-reject [fallback-on-reject]**

**Command mode:** config

**Hierarchies**

- system aaa-server

**Note**
- If fallback-on-reject is enabled, authentication will be performed against the secondary method (if configured) if the first method attempt is rejected
- If fallback-on-reject is disabled, authentication will be performed against the secondary method (if configured) only if the first method is not available

**Parameter table**

+--------------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter          | Description                                                                      | Range        | Default  |
+====================+==================================================================================+==============+==========+
| fallback-on-reject | When enabled, this option allows fallback on secondary authentication method as  | | enabled    | disabled |
|                    | configured by authentication-order if the first one is rejected                  | | disabled   |          |
+--------------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# aaa-server
    dnRouter(cfg-system-aaa)# fallback-on-reject enabled


**Removing Configuration**

To revert the fallback-on-reject to default:
::

    dnRouter(system-aaa-tacacs)# no fallback-on-reject

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| v18.3   | Command introduced |
+---------+--------------------+
