interfaces ndp router-advertisement install-default-route
---------------------------------------------------------

**Minimum user role:** operator

If set, install an IPv6 default route to router next-hop as result of receiving valid router-advertisement on this interface.
To set install-default-route:

**Command syntax: install-default-route**

**Command mode:** config

**Hierarchies**

- interfaces ndp router-advertisement

**Note**
- The command is applicable only if ipv6-admin-state is enabled 

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# irb1
    dnRouter(cfg-if-irb1)# ndp router-advertisement
    dnRouter(cfg-if-irb1-ndp-ra)# install-default-route


**Removing Configuration**

To clear install-default-route behavior:
::

    dnRouter(cfg-if-irb1-ndp-ra)# no install-default-route

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
