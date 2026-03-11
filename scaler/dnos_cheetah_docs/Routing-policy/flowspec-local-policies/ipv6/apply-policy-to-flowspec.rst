routing-policy flowspec-local-policies ipv6 apply-policy-to-flowspec
--------------------------------------------------------------------

**Minimum user role:** operator

Specifys which of the policies that were defined for IPv6, that should be installed - only one policy may be installed.

**Command syntax: apply-policy-to-flowspec [apply-to-flowspec-policy-name]**

**Command mode:** config

**Hierarchies**

- routing-policy flowspec-local-policies ipv6

**Parameter table**

+-------------------------------+----------------------------------------------------------------------------------+--------+---------+
| Parameter                     | Description                                                                      | Range  | Default |
+-------------------------------+----------------------------------------------------------------------------------+--------+---------+
| apply-to-flowspec-policy-name | The name of ipv6 policy to install - only a single ipv6 policy may be installed. | string | \-      |
|                               |                                                                                  | length |         |
|                               |                                                                                  | 1..255 |         |
+-------------------------------+----------------------------------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# flowspec-local-policies
    dnRouter(cfg-rpl-flp)# ipv6
    dnRouter(cfg-rpl-flp-ipv6)# apply-policy-to-flowspec policy-1
    dnRouter(cfg-rpl-flp-ipv6)#


**Removing Configuration**

To remove the policy that was installed.
::

    dnRouter(cfg-rpl-flp-ipv6)# no apply-policy-to-flowspec policy-1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
