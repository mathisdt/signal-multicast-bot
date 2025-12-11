# Signal Multicast Bot

This project makes use of a Postgres database and [signal-cli](https://github.com/AsamK/signal-cli)
to create a service similar to what moderated mailing lists provided some years ago, but on Signal: 

- administrators create lists
- users subscribe to them or are added by administrators
- administrators send messages which are distributed to all subscribers

Signal already has groups, but this is made for announcement-like communication. The users
don't know who else is on the list, and everyone gets the messages in a one-to-one chat.

### Bot commands

#### Basic (everyone can send these commands to the bot)
```
bot help
bot subscribe <GROUPNAME> <PARTICIPANT NAME>
bot unsubscribe <GROUPNAME>
```

#### Administrative (only select people can use these commands)

```
bot listgroups
bot addgroup <GROUPNAME>
bot removegroup <GROUPNAME>
bot list <GROUPNAME>
bot add <GROUPNAME> <PARTICIPANT PHONE NUMBER WITHOUT SPACES> <PARTICIPANT NAME>
bot remove <GROUPNAME> <PARTICIPANT NAME OR NUMBER>
bot send <GROUPNAME> <SOME TEXT>
```

#### Examples

```
bot subscribe Testgroup Steven Miller
bot addgroup Testgroup
bot add Testgroup 017912345678 Some Dude
bot send Testgroup This message should be sent!
```

### Get started

1. If you don't have a [Postgres](https://www.postgresql.org) instance yet, create one.
2. If you don't run [signal-cli as DBus service](https://github.com/AsamK/signal-cli/wiki/DBus-service)
   yet, set it up now.
3. Checkout this project to your computer (or just copy `main.py`, `database.py` and `config-template.ini`).
4. Copy `config-template.ini` to `config.ini` and edit it so it contains 
   the phone number(s) you want to use and the correct database credentials.
5. Call `main.py` with at least Python 3.6 installed.

## License

This project is licensed under GPL v3. If you submit or contribute changes, these are automatically licensed
under GPL v3 as well. If you don't want that, please don't submit the contribution (e.g. pull request)!
