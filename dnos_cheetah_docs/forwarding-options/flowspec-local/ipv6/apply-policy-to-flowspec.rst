forwarding-options flowspec-local ipv6 apply-policy-to-flowspec
---------------------------------------------------------------

**Minimum user role:** operator

Specify which of the policies that were defined for IPv6 should be installed - only one policy may be installed.

**Command syntax: apply-policy-to-flowspec [apply-to-flowspec-policy-name]**

**Command mode:** config

**Hierarchies**

- forwarding-options flowspec-local ipv6

**Parameter table**

+-------------------------------+-----------------------------------------------------------------------------+------------------+---------+
| Parameter                     | Description                                                                 | Range            | Default |
+===============================+=============================================================================+==================+=========+
| apply-to-flowspec-policy-name | name of ipv6 policy to install - only a single ipv6 policy may be installed | | string         | \-      |
|                               |                                                                             | | length 1-255   |         |
+-------------------------------+-----------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# flowspec-local-policies
    dnRouter(cfg-rpl-flp)# ipv6
    dnRouter(cfg-rpl-flp-ipv6)# apply-policy-to-flowspec policy-1
    dnRouter(cfg-rpl-flp-ipv6)#


**Removing Configuration**

To remove the installed policy:
::

    dnRouter(cfg-rpl-flp-ipv6)# no apply-policy-to-flowspec policy-1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
