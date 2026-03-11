help menu command
-----------------

The CLI includes context sensitive help that displays a list of options available at the current hierarchy with a short description. To access the context-sensitive help, press ? . You can also use the tab key for assistance.

Use the tab key to:

- Show all commands that are available under the current prompt - press tab at the prompt.

**Note**

- Help is not available for user-configured aliases.

**Example**
::

	dnRouter# tab
	clear
	configure
	no
	request
	run
	set
	show
	end
	exit
	quit
	top
	dnRouter#

- Show available options for a specific command - enter tab after entering a complete command name.

**Example**
::

	dnRouter# show tab
	access-list
	arp
	...
	dnRouter# show

- Auto-complete a partially entered command - press tab after entering part of a command name (with no space in between).

**Example**
::

	dnRouter# show inttab
	dnRouter# show interfaces

- If the partially entered command is not unique, auto-complete will not work. You need to enter enough of the command to disambiguate it.

**Example**

Won't work (because ip is used by both ipv4-address and ipv6-address commands):

::

	dnRouter(cfg)# interfaces ge100-1/1/1 iptab
	dnRouter(cfg)#

Will work:

::

	dnRouter(cfg)# interfaces ge100-1/1/1 ipv4tab
	dnRouter(cfg)# interfaces ge100-1/1/1 ipv4-address

- In configuration mode, a separator is displayed between the hierarchy specific command items, i.e. the list of commands that are specific to the current hierarchy, and general command items, i.e. the commands that are applicable to all hierarchy levels and are not specific to the current hierarchy.

**Example**
::

  SECOND(cfg)# services
  SECOND(cfg-srv)
  flow-monitoring           Configure flow-monitoring
  l2-cross-connect          Enters the context of L2 cross connect service configuration.
  mpls-oam                  Configure mpls-oam profile
  port-mirroring            Configure a new port-mirroring session.
  twamp                     Configure TWAMP service

 ----------------

  clear                     Clear command
  commit                    Commit transaction
  dump                      Generate a core dump of BGP process without killing it
  end                       Exit configuration menu
  exit                      Exit current menu
  load                      Load saved configuration
  quit                      Quit DRIVENETS CLI
  request                   Request operations
  rollback                  Rollback transaction
  run                       Run a command
  save                      Save current configuration
  set                       Set temporary configuration
  show                      Displays information about the system and system configuration
  top                       Exit to root configuration menu
  unset                     Unset temporary configuration
