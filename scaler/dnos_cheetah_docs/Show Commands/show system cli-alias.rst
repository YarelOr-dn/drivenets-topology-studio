show system cli-alias 
---------------------

**Minimum user role:** viewer

To display a list of all configured aliases:



**Command syntax: show system cli-alias**

**Command mode:** operational



.. **Note**

	- output shown according alias-key alphabetically

	- output will show none if no alias configured


**Example**
::

	dnRouter# show system cli-alias

	cli-alias sint "show interfaces"

	cli-alias sbs "show bgp summary"
	

.. **Help line:** show list of all configured aliases

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+

