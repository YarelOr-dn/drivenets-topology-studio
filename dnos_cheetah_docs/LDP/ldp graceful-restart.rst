ldp graceful-restart
--------------------

**Minimum user role:** operator

LDP graceful restart enables a router to continue forwarding traffic while its LDP control plane is restarting. It also enables a helper router to assist a peer that is attempting to restart LDP.
To enter LDP graceful restart configuration level:

**Command syntax: graceful-restart**

**Command mode:** config

**Hierarchies**

- protocols ldp

**Note**

- Notice the change in prompt. 

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# ldp
	dnRouter(cfg-protocols-ldp)# graceful-restart
	dnRouter(cfg-protocols-ldp-gr)#

**Removing Configuration**

To revert the graceful-restart parameters to their default values:
::

	dnRouter(cfg-protocols-ldp)# no graceful-restart

.. **Help line:** Enters LDP Graceful Restart configuration level

**Command History**

+-------------+-------------------------------------------------+
|             |                                                 |
| Release     | Modification                                    |
+=============+=================================================+
|             |                                                 |
| 6.0         | Command introduced                              |
+-------------+-------------------------------------------------+
|             |                                                 |
| 13.0        | Command split into three additional commands    |
+-------------+-------------------------------------------------+