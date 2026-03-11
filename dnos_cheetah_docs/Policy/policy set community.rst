policy set community
--------------------

**Minimum user role:** operator

Use this command to add or remove communities for BGP updates. When you enter multiple entries, they are collected as a list. You can add or remove values to/from the list, and you can do this in separate commits.

To set the specified communities value to BGP updates:


**Command syntax: set community {**  additive **[community],** [community], . **\| none }**

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Note**

- You can set up to 25 different communities or 'none'.

- The command cannot be set together with "set community-list".

- Running one of these commands will replace whatever was previously configured.


**Parameter table**

+---------------+-------------------------------------------------------------------------------------------------+----------------------------------------------------------+---------------------+
|               |                                                                                                 |                                                          |                     |
| Parameter     | Description                                                                                     | Range                                                    | Comment             |
+===============+=================================================================================================+==========================================================+=====================+
|               |                                                                                                 |                                                          |                     |
| community     | The community value to set to BGP updates.                                                      | The community number (e.g. aa:nn), range (e.g. aa-bb:nn) | AS_number: 1..65535 |
|               |                                                                                                 |                                                          |                     |
|               | The set community [community] command will replace any existing community configuration.        | <AS_number:NN>                                           | ID: 0..65535        |
|               |                                                                                                 |                                                          |                     |
|               |                                                                                                 | <lower_AS_number- upper_AS_number:lower_id-upper-id>     |                     |
|               |                                                                                                 |                                                          |                     |
|               |                                                                                                 | internet                                                 |                     |
|               |                                                                                                 |                                                          |                     |
|               |                                                                                                 | accept-own                                               |                     |
|               |                                                                                                 |                                                          |                     |
|               |                                                                                                 | local-AS                                                 |                     |
|               |                                                                                                 |                                                          |                     |
|               |                                                                                                 | no-export                                                |                     |
|               |                                                                                                 |                                                          |                     |
|               |                                                                                                 | no-advertise                                             |                     |
|               |                                                                                                 |                                                          |                     |
|               |                                                                                                 | no-LLGR                                                  |                     |
|               |                                                                                                 |                                                          |                     |
|               |                                                                                                 | LLGR-stale                                               |                     |
+---------------+-------------------------------------------------------------------------------------------------+----------------------------------------------------------+---------------------+
|               |                                                                                                 |                                                          |                     |
| additive      | Appends the new communities to the existing communities.                                        |  \-                                                      | \-                  |
+---------------+-------------------------------------------------------------------------------------------------+----------------------------------------------------------+---------------------+
|               |                                                                                                 |                                                          |                     |
| none          | Removes the entire communities attribute from BGP updates.                                      |  \-                                                      | \-                  |
|               |                                                                                                 |                                                          |                     |
|               | The set community none will overwrite any existing community with "none".                       |                                                          |                     |
+---------------+-------------------------------------------------------------------------------------------------+----------------------------------------------------------+---------------------+

**Example**

To overwrite the existing route communities with new communities:
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy SET_FULL_ROUTES
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)# set community 65000:1918

	dnRouter(cfg-rpl-policy)# rule 20 allow
	dnRouter(cfg-rpl-policy-rule-20)# set community 65000:86, 65000:2010
	dnRouter(cfg-rpl-policy)# rule 30 allow
	dnRouter(cfg-rpl-policy-rule-30)# set community local-AS, 65000:2010, internet

To add new route communities to the existing communities:
::

	dnRouter(cfg-rpl-policy)# rule 50 allow
	dnRouter(cfg-rpl-policy-rule-50)# set community additive 65000:86, 65000:2010

To delete the existing route communities (by overwriting them with "none")
::

	dnRouter(cfg-rpl-policy)# rule 40 allow
	dnRouter(cfg-rpl-policy-rule-40)# set community none

**Removing Configuration**

To remove the set entry:
::

	dnRouter(cfg-rpl-policy-rule-10)# no set community


.. **Help line:** The specified communities value is set to BGP updates.


**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
| 6.0         | Command introduced    |
+-------------+-----------------------+
| 18.2        | Added note for command|
|             | restriction           |
+-------------+-----------------------+
| 18.2        | Impose action order   |
|             | within route policy   |
|             | rule                  |
+-------------+-----------------------+