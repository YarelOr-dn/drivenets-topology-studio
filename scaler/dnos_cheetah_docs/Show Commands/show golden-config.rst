show golden-config
------------------

**Minimum user role:** viewer

To view an output of the golden configuration file saved to the system:

**Command syntax: show golden-config**

**Command mode:** operational


**Note**

- The output of this command displays the configuration saved to the golden-config file.

- Notice the square brackets, for example in: interfaces ge100-1/1/1 mpls enabled [disabled]. The default admin-value of mpls under interface is "disabled", however, for this interface MPLS is enabled.

- The configuration output is wrapped with **start** and **end** clauses as follows:

::

	# <system-name> golden-config-start

	...

	# <system-name> golden-config-end

..
	**Internal Note**
	- Proper indications should be returned as part of CLI command output in case the configuration file does not exist or cannot be read.
	- CLI show command operation should also perform file syntax validity checks (e.g., check it includes DNOS version, check xml/json format)

**Example**
::

	dnRouter# show golden-config

	# dnRouter golden-config-start

	system
	  name dnRouter
	  login
	    user RootUser
	      description MyrootUser
	    !
	  !
	!

	interfaces
	  ge100-1/1/1
	    mtu 9200
	    mpls enabled
	  !
	  bundle-2
	    mtu 9200
	    mpls enabled
	  !
	!

	#dnRouter golden-config-end

	dnRouter# show golden-config
	Warning: could not find golden-config file

	dnRouter# show golden-config
	Warning: golden-config file failed sytanx checks and may be corrupted

.. **Help line:** show golden configuration

**Command History**

+---------+----------------------------------------------------------+
| Release | Modification                                             |
+=========+==========================================================+
| 19.1    | Command introduced                                       |
+---------+----------------------------------------------------------+
