nacm rule-list rule action
--------------------------

**Minimum user role:** admin

The access control action associated with the rule. If a rule has been determined to match a particular request, then this object is used to determine whether to permit or deny the request. To configure the access control action:

**Command syntax: action [action]**

**Command mode:** config

**Hierarchies**

- nacm rule-list rule

**Parameter table**

+-----------+----------------------------------------------------------------------------------+------------+---------+
| Parameter | Description                                                                      | Range      | Default |
+===========+==================================================================================+============+=========+
| action    | The access control action associated with the rule.  If a rule has been          | | permit   | \-      |
|           | determined to match a particular request, then this object is used to determine  | | deny     |         |
|           | whether to permit or deny the request.                                           |            |         |
+-----------+----------------------------------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# nacm
    dnRouter(cfg-nacm)# rule-list <name>
    dnRouter(cfg-nacm-rulist)# rule <name>
    dnRouter(cfg-nacm-rulist-rule)# action deny


**Removing Configuration**

To revert the action request:
::

    dnRouter(cfg-nacm-rulist-rule)# no action

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
