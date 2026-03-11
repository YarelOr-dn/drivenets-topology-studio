routing-policy policy rule set nhc-entropy-label
------------------------------------------------

**Minimum user role:** operator

When set on a given BGP route path nhc-entropy-label disabled, it is required to remove the request for an entropy label. Applicable for ipv4-unicast labeled-unicast and ipv6-unicast labeled-unicast address families

**Command syntax: set nhc-entropy-label [nhc-entropy-label]**

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Parameter table**

+-------------------+---------------------------+----------+---------+
| Parameter         | Description               | Range    | Default |
+===================+===========================+==========+=========+
| nhc-entropy-label | Set the nhc entropy-label | disabled | \-      |
+-------------------+---------------------------+----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# policy MY_POLICY
    dnRouter(cfg-rpl-policy)# rule 10 allow
    dnRouter(cfg-rpl-policy-rule-10)# set nhc-entropy-label disabled


**Removing Configuration**

To remove set protocols criteria:
::

    dnRouter(cfg-rpl-policy-rule-10)# no set nhc-entropy-label

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
