system netconf response-envelope
--------------------------------

**Minimum user role:** operator

Enter the NETCONF response-envelope configuration.

**Command syntax: response-envelope**

**Command mode:** config

**Hierarchies**

- system netconf

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# netconf
    dnRouter(cfg-system-netconf)# response-envelope
    dnRouter(cfg-netconf-response-envelope)#


**Removing Configuration**

To revert the response-envelope configuration to default:
::

    dnRouter(cfg-system-netconf)# no response-envelope

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
