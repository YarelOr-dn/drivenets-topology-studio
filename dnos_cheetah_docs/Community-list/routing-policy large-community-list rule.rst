routing-policy large-community-list rule
----------------------------------------

**Minimum user role:** operator

To configure rules for large community lists:

**Command syntax: rule [rule-id] [rule-type] {value [large-community] | regex [regex] }**

**Command mode:** config

**Hierarchies**

- routing policy large community list

**Parameter table**

+--------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------+---------+
|                    |                                                                                                                                                                                                                  |                          | Default |
| Parameter          | Description                                                                                                                                                                                                      | Range                    |         |
+====================+==================================================================================================================================================================================================================+==========================+=========+
|                    |                                                                                                                                                                                                                  |                          | \-      |
| rule-id            | The rule's unique identifier within the community list. It determines the priority of the rule (rules with a low ID number have priority over rules with high ID numbers). You must configure at least one rule. | 1..65534                 |         |
|                    |                                                                                                                                                                                                                  |                          |         |
|                    | The default ID (65535) is assigned by the system to "Deny any" when no match is found.                                                                                                                           |                          |         |
|                    |                                                                                                                                                                                                                  |                          |         |
|                    | When configuring a rule ID that is already in use, all of the   original rules' entries are overwritten.                                                                                                         |                          |         |
+--------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------+---------+
|                    |                                                                                                                                                                                                                  |                          | \-      |
| rule-type          | Defines whether the traffic matching the rule conditions are to be   allowed or denied.                                                                                                                          | allow                    |         |
|                    |                                                                                                                                                                                                                  |                          |         |
|                    |                                                                                                                                                                                                                  | deny                     |         |
+--------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------+---------+
|                    |                                                                                                                                                                                                                  |                          | \-      |
| large community    | <AS_number\:id-1\:id-2>                                                                                                                                                                                          | AS_number: 0..4294967295 |         |
|                    |                                                                                                                                                                                                                  |                          |         |
|                    |                                                                                                                                                                                                                  | ID-1: 0..4294967295      |         |
|                    |                                                                                                                                                                                                                  | ID-2: 0..4294967295      |         |
+--------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------+---------+
|                    |                                                                                                                                                                                                                  | \-                       | \-      |
| regex              | A regular expression defining a search pattern to match large communities attribute in BGP updates.                                                                                                              |                          |         |
|                    |                                                                                                                                                                                                                  |                          |         |
+--------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# large-community-list CL_NAME
	dnRouter(cfg-rpl-lcl)# rule 10 allow value 15562:45:29
	dnRouter(cfg-rpl-lcl)# rule 20 allow regex 65000:*:5000

**Removing Configuration**

To remove a rule entry:
::

	dnRouter(cfg-rpl-lcl)# no rule 20

.. Help line:** add large community to large community list

**Command History**

+-----------+-----------------------+
| Release   | Modification          |
+===========+=======================+
| 15.1      | Command introduced    |
+-----------+-----------------------+