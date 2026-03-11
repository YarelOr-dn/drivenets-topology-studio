services performance-monitoring simple-twamp session profile
------------------------------------------------------------

**Minimum user role:** operator

To associate a configuration profile for the Simple TWAMP monitoring session:

**Command syntax: profile [profile-name]**

**Command mode:** config

**Hierarchies**

- services performance-monitoring simple-twamp session

**Parameter table**

+--------------+----------------------------------------------------------------------+------------------+---------+
| Parameter    | Description                                                          | Range            | Default |
+==============+======================================================================+==================+=========+
| profile-name | The Simple TWAMP profile containing session parameters configuration | | string         | default |
|              |                                                                      | | length 1-255   |         |
+--------------+----------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# simple-twamp session Session-1
    dnRouter(cfg-srv-pm-stamp-session)# profile Daily-Monitoring


**Removing Configuration**

To revert to the default configuration profile for the Simple TWAMP monitoring session:
::

    dnRouter(cfg-srv-pm-stamp-session)# no profile

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
