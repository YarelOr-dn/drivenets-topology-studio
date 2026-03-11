commit log
----------

**Minimum user role:** operator

You can add a description of the committed configuration. The added comment is displayed in the show rollback output to help you identify the content of the commit.

To add a comment that describes the committed configuration:

**Command syntax: commit** [action] log [comment]

**Command mode:** operational

**Note**

- The log flag is applicable only to the "commit" and "commit and-quit" commands.

**Parameter table**
+-----------+-----------------------------------------------+--------------+---------+
| Parameter | Description                                   | Range        | Default |
+-----------+-----------------------------------------------+--------------+---------+
| action    | Enter the commit action that you want to run. | none         | \-      |
|           |                                               | and-exit     |         |
|           |                                               | and-confirm  |         |
+-----------+-----------------------------------------------+--------------+---------+
| comment   | Enter a comment that describes the commit.    | 1..512 bytes | \-      |
+-----------+-----------------------------------------------+--------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# interface bundle-1 mac-address 00:00:00:00:00:01
	dnRouter(cfg)# commit and-quit log my first commit
	Commit succeeded by ADMIN at 27-Jan-2017 22:11:00 UTC
	dnRouter#


.. **Help line:** Add a comment that describes the committed configuration

**Command History**

+---------+-------------------------+
| Release | Modification            |
+---------+-------------------------+
| 10.0    | Command introduced      |
+---------+-------------------------+
| 17.1    | Updated range parameter |
+---------+-------------------------+
