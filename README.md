# Signal Multicast Bot

This project makes use of a [Postgres database](https://www.postgresql.org) and 
[signal-cli via DBus](https://github.com/AsamK/signal-cli/wiki/DBus-service) to create a service
similar to what moderated mailing lists provided some years ago: 

- administrators create lists
- users subscribe to them
- administrators send messages which are distributed to all subscribers

### Get started

1. If you don't have a Postgres instance yet, create one.
2. If you don't run signal-cli as DBus service yet, set it up now.
3. Checkout this project to your computer (or just copy `main.py`, `database.py` and `config-template.ini`).
4. Copy `config-template.ini` to `config.ini` and edit it so it contains 
   the phone number(s) you want to use and the correct database credentials.
5. Call `main.py` with at least Python 3.6 installed.
