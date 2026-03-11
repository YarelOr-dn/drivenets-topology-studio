Copy paste for show commands
----------------------------

Multiple copy/paste for show commands are enabled by DNOS cli (for example, copying 10 "show system version" commands will result to 10 outputs of the command).

In case the show command output needs to be paged (for cases the output contains numerous lines), then the pager will start and all following commands will be ignored. Meaning there will not be a way to paste multiple show commands once a command needs a pager.
