services performance-monitoring interface delay-measurement dynamic-delay profile
---------------------------------------------------------------------------------

**Minimum user role:** operator

To associate a configuration profile for the dynamic link delay monitoring session:

**Command syntax: profile [profile-name]**

**Command mode:** config

**Hierarchies**

- services performance-monitoring interface delay-measurement dynamic-delay

**Parameter table**

+--------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter    | Description                                                                      | Range            | Default |
+==============+==================================================================================+==================+=========+
| profile-name | The Simple TWAMP link-performance profile containing session parameters          | | string         | default |
|              | configuration                                                                    | | length 1-255   |         |
+--------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# interface ge100-0/0/0
    dnRouter(cfg-srv-pm-ge100-0/0/0)# delay-measurement
    dnRouter(cfg-pm-ge100-0/0/0-dm)# dynamic-delay
    dnRouter(cfg-ge100-0/0/0-dm-dynamic-delay)# profile daily-monitoring
    dnRouter(cfg-ge100-0/0/0-dm-dynamic-delay)#


**Removing Configuration**

To revert to the default configuration profile for the dynamic link delay monitoring session:
::

    dnRouter(cfg-ge100-0/0/0-dm-dynamic-delay)# no profile

**Command History**

+---------+------------------------------------+
| Release | Modification                       |
+=========+====================================+
| 18.0    | Command introduced                 |
+---------+------------------------------------+
| 18.2    | removed the 'interfaces' hierarchy |
+---------+------------------------------------+
