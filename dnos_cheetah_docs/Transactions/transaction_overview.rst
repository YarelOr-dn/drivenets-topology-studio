Transaction Commands
--------------------

You need to commit your changes to save them to the database and for them to
take operational effect. DNOS supports configuration transactions, enabling
multiple users to simultaneously configure the system. Every transaction
receives a unique identifier. All user performed actions are saved as a
candidate configuration until the configuration is committed. This allows to
verify the configuration without impacting the running configuration. This
also enables to roll back to a previous configuration, even after commit.

<INSERT 01_transactions>

In the above example, the running configuration ID is #1. User A performs
changes to the configuration. The changes are saved to a candidate
configuration 1A. When User A commits the changes, the changes are merged to
the running configuration with a new ID #2.

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

The NCC maintains an object relational mapping database (ORM DB) that holds
the configuration. The ORM DB is replicated on the standby NCC and is updated
with new commits. At NCC switchover, the standby NCC (now active ) is ready
with the most recent configuration.

<INSERT 03_transactions>

Changes made by multiple concurrent users are saved in separate candidate
configuration files. The first user to commit will not encounter any conflict
during commit. Subsequent users may encounter such conflict, if their
candidate configuration conflicts with the committed configuration. For
example (see image below), if User A makes configuration changes to its Cand
2A and deletes an interface X while User B changes the IP address of interface
X in Cand 2B and User A commits first, User B's IP change cannot be committed.
In this case, User B will be notified of the conflict and will be prompted to
revise or cancel the configuration. Only after the conflict is resolved, will
User B be allowed to merge the Cand B changes to the v3 running configuration.

<INSERT 04_transactions>

If after User A successfully commits changes, User C begins to make changes to
the configuration (on configuration ID #3) and commits, Cand 3C will not
conflict, even though Cand 2B may not yet be resolved.

<INSERT 05_transactions>

It is good practice to run the show config command or commit check to check
the configuration before committing a new configuration. These commands
trigger the committed changes and you will be notified of any conclicts that
may arise during commit.

You can abort a commit using the Ctrl+C keyboard shortcut. You will be
prompted to confirm the abort operation.

If during the commit a fail occurs that causes the NCC reset, the NCC will be
loaded with the last successfully committed configuration.

**Note:** If the SSH session terminates during the commit, the commit will
proceed.

To save your changes to the configuration, use the "commit" transaction
commands in configuration mode:

+----------+--------------------------------------------------------------------------------------------------------------------------------+
| Option   | Description                                                                                                                    |
+----------+--------------------------------------------------------------------------------------------------------------------------------+
| commit   | Applies changed configuration.                                                                                                 |
+----------+--------------------------------------------------------------------------------------------------------------------------------+
| check    | Verifies that the candidate configuration is syntactically correct, but does not commit the changes.                           |
+----------+--------------------------------------------------------------------------------------------------------------------------------+
| confirm  | Confirms the commit and applies it immediately.                                                                                |
+----------+--------------------------------------------------------------------------------------------------------------------------------+
| and-quit | Commits the configuration and, if the configuration contains no errors and the commit succeeds, exits from configuration mode. |
+----------+--------------------------------------------------------------------------------------------------------------------------------+
| log      | Adds a comment that describes the committed configuration                                                                      |
+----------+--------------------------------------------------------------------------------------------------------------------------------+