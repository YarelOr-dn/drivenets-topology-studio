routing-policy policy rule set as-path exclude from to
------------------------------------------------------

**Minimum user role:** operator

Remove any as number from the as-path that falls in the provided range.
To exclude the specified as-number(s) from the as-path:

**Command syntax: set as-path exclude from [set-as-path-exclude-from] to [set-as-path-exclude-to]**

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Note**

- Within the same route policy rule, "set as-path exclude from to" will be processed and imposed before "set as-path prepend" action.

- Can be set in the same rule with "set as-path exclude <as-path list>". All as numbers requested by the two set cmds will be removed from the as-path.

- The removed as number does not have to be sequential on the as the path, e.g., for as-path = ‘67 65534 100 65533 5 78 89 90’ and imposing "set as-path exclude from 65533 to 65534" the resulting as-path will be ‘67 100 5 78 89 90’.

- Commit validation required that to >= from. Can support set as-path to exclude from X to X to impose specific as-number removal.

**Parameter table**

+--------------------------+----------------------------------------------------------+--------------+---------+
| Parameter                | Description                                              | Range        | Default |
+==========================+==========================================================+==============+=========+
| set-as-path-exclude-from | Starting range for as-numbers to be removed from as-path | 1-4294967295 | \-      |
+--------------------------+----------------------------------------------------------+--------------+---------+
| set-as-path-exclude-to   | End range for as-numbers to be removed from as-path      | 1-4294967295 | \-      |
+--------------------------+----------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# policy MY_POLICY
    dnRouter(cfg-rpl-policy)# rule 10 allow
    dnRouter(cfg-rpl-policy-rule-10)# set as-path exclude from 65000 to 65535


**Removing Configuration**

To remove set action:
::

    dnRouter(cfg-rpl-policy-rule-10)# no set as-path exclude from

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
