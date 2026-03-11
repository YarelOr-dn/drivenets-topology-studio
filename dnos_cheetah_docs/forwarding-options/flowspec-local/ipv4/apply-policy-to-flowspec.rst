forwarding-options flowspec-local ipv4 apply-policy-to-flowspec
---------------------------------------------------------------

**Minimum user role:** operator

Specifies which of the policies that were defined for IPv4 should be installed - only one policy may be installed. To specify the policy to be installed:

**Command syntax: apply-policy-to-flowspec [apply-to-flowspec-policy-name]**

**Command mode:** config

**Hierarchies**

- forwarding-options flowspec-local ipv4

**Parameter table**

+-------------------------------+-----------------------------------------------------------------------------+------------------+---------+
| Parameter                     | Description                                                                 | Range            | Default |
+===============================+=============================================================================+==================+=========+
| apply-to-flowspec-policy-name | name of ipv4 policy to install - only a single ipv4 policy may be installed | | string         | \-      |
|                               |                                                                             | | length 1-255   |         |
+-------------------------------+-----------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# forwarding-options
    dnRouter(cfg-fwd_opts)# ipv4
    dnRouter(cfg-fwd_opts-ipv4)# apply-policy-to-flowspec policy-1


**Removing Configuration**

To remove the installed policy:
::

    dnRouter(cfg-fwd_opts-ipv4)# no apply-policy-to-flowspec

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
