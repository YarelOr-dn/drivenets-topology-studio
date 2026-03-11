system ntp authentication key
-----------------------------

**Minimum user role:** operator

To configure a NTP authentication key:

**Command syntax: authentication key [authentication-key]**

**Command mode:** config

**Hierarchies**

- system ntp

**Parameter table**

+--------------------+------------------------+---------+---------+
| Parameter          | Description            | Range   | Default |
+====================+========================+=========+=========+
| authentication-key | NTP authentication key | 1-65533 | \-      |
+--------------------+------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ntp
    dnRouter(cfg-system-ntp)# authentication key <authentication-key>


**Removing Configuration**

To remove the specified NTP authentication key:
::

    dnRouter(cfg-system-ntp-authentication)# no key 1242151523

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
