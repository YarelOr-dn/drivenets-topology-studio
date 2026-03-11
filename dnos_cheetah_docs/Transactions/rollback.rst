rollback
--------

**Minimum user role:** operator

Each successful commit generates a transaction file with a rollback-id. You
can use this rollback-id to rollback the configuration in a specific
transaction file (undoing subsequent commits).

When a new commit is performed, the new commit (now the new running
configuration) receives the rollback-id 0 and the rollback-id of every
previous commit increases by 1. The system saves 50 rollback files (in
addition to rollback-0, which is the running configuration). When the
rollback-id pool is full, the oldest commit (rolback-id 50) is removed to make
room for the new commit (i.e. first-in-first-out).

<INSERT 02_transactions>

Each rollback file contains the following information:

-	Date and time

-	System version

-	User name (the user who initiated the change)

-	Optional logging comment

The rollback action loads the configuration to the candidate database. It is
not automatically committed.

To roll back to a saved transaction:


**Command syntax: rollback** [rollback-id]

**Command mode:** operational

**Note**

- Rollback 0 returns to the current configuration.

..
	**Internal Note**

	- No broadcasting to other users

**Parameter table**

+----------------+--------------------------------------------------------------+-----------+-------------+
| Parameter      | Description                                                  | Range     | Default     |
+================+==============================================================+===========+=============+
| rollback-id    | The unique identifier for each committed configuration.      | 0..49     | 0           |
+----------------+--------------------------------------------------------------+-----------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# rollback 10
	Configuration rollback complete

.. **Help line:** Rollback to a saved transaction file

**Command History**

+-------------+-----------------------+
| Release     | Modification          |
+=============+=======================+
| 6.0         | Command introduced    |
+-------------+-----------------------+