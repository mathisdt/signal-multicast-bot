#!/usr/bin/env python3

import atexit
import configparser
import logging
import os.path
import re

from gi.repository import GLib
from pydbus import SystemBus

from database import Database

NEWLINE = "\n"

logging.basicConfig(encoding='utf-8', level=logging.DEBUG)

if not os.path.isfile("config.ini"):
    logging.error(
        "config.ini not found - maybe you didn't copy (and customize) the file config-template.ini to config.ini yet?")
    exit(1)

config = configparser.ConfigParser()
config.read("config.ini")
logging.debug("configuration read")

bot_basic_command = re.compile(
    "(?i)(?s)^ *bot +(help|subscribe|unsubscribe)(?: +([a-z0-9]+)(?: +(.*))?)? *$")
bot_administrative_command = re.compile(
    "(?i)(?s)^ *bot +(listgroups|addgroup|removegroup|list|add|remove|send)(?: +([a-z0-9]+)(?: +(.*))?)? *$")
bus = SystemBus()
loop = GLib.MainLoop()

signal = bus.get('org.asamk.Signal', object_path=f'/org/asamk/Signal/_{config["signal"]["number"]}')
db = Database(config)


def exit_handler():
    db.close()


def send_msg(recipient, message):
    signal.sendMessage(message, [], [recipient], signature="sasas")


def with_country_code(phone_number):
    return re.sub("^0", f'+{config["signal"]["default_country_code"]}', phone_number)


def execute_basic_cmd(source, command, group, name):
    if command == "help":
        try:
            send_msg(source, "available commands (GROUPNAME may not contain any spaces):\n\n"
                             "---> basic (everyone can send these commands to the bot):\n\n"
                             "bot help\n"
                             "bot subscribe <GROUPNAME> <PARTICIPANT NAME>\n"
                             "bot unsubscribe <GROUPNAME>\n\n"
                             "---> administrative (only select people can use these commands):\n\n"
                             "bot listgroups\n"
                             "bot addgroup <GROUPNAME>\n"
                             "bot removegroup <GROUPNAME>\n"
                             "bot list <GROUPNAME>\n"
                             "bot add <GROUPNAME> <PARTICIPANT PHONE NUMBER WITHOUT SPACES> <PARTICIPANT NAME>\n"
                             "bot remove <GROUPNAME> <PARTICIPANT NAME OR NUMBER>\n"
                             "bot send <GROUPNAME> <SOME TEXT>\n\n"
                             "---> examples:\n\n"
                             "bot subscribe Testgroup Steven Miller\n"
                             "bot addgroup Testgroup\n"
                             "bot add Testgroup 017912345678 Some Dude\n"
                             "bot send Testgroup This message should be sent!")
        except Exception as e:
            send_msg(source, f"could not list groups: {e}")
    elif command == "subscribe":
        try:
            if name is None or len(name) == 0:
                raise Exception("you didn't supply your name after the groupname")
            gr = db.group(group_name=group)
            phone = with_country_code(source)
            db.member_add(group_id=gr[0], member_phone=phone, member_name=name)
            logging.debug(f"subscribe: added {phone} {name} to group {gr[1]}")
            send_msg(source, f"added you ({phone} alias {name}) to group {gr[1]}")
        except Exception as e:
            logging.warning(f"subscribe: could not add {source} to group {group}: {e}")
            send_msg(source, f"could not add you to {group}: {e}")
    elif command == "unsubscribe":
        try:
            gr = db.group(group_name=group)
            phone = with_country_code(source)
            db.member_remove(group_id=gr[0], member_phone=phone)
            logging.debug(f"unsubscribe: remove {phone} from group {gr[1]} ")
            send_msg(source, f"deleted you ({phone}) from group {gr[1]} if you were a member")
        except Exception as e:
            logging.warning(f"unsubscribe: could not delete {source} from group {group}: {e}")
            send_msg(source, f"could not delete you from {group}: {e}")


def execute_admin_cmd(source, command, group, param):
    if command == "listgroups":
        try:
            groups = db.groups()
            group_names = list(map(lambda g: g[1], groups))
            logging.debug(f"listgroups: called by {source}")
            send_msg(source, f"available groups:\n\n{', '.join(group_names)}")
        except Exception as e:
            logging.warning(f"listgroups: called by {source}, exception {e}")
            send_msg(source, f"could not list groups: {e}")
    elif command == "addgroup":
        try:
            db.group_add(group_name=group)
            logging.debug(f"addgroup {group}: called by {source}")
            send_msg(source, f"group {group} created")
        except Exception as e:
            logging.warning(f"addgroup {group}: called by {source}, exception {e}")
            send_msg(source, f"could not create group {group}: {e}")
    elif command == "removegroup":
        try:
            gr = db.group(group_name=group)
            members = db.group_members(group_id=gr[0])
            members_as_strings = list(map(lambda g: f"{g[0]} {g[1]}", members))
            db.group_remove(group_name=group)
            logging.debug(f"removegroup {group}: called by {source}")
            send_msg(source, f'group {gr[1]} deleted including its {len(members)} members:\n\n'
                             f'{NEWLINE.join(members_as_strings)}')
        except Exception as e:
            logging.warning(f"removegroup {group}: called by {source}, exception {e}")
            send_msg(source, f"could not delete group {group}: {e}")
    elif command == "list":
        try:
            gr = db.group(group_name=group)
            members = db.group_members(group_id=gr[0])
            members_as_strings = list(map(lambda g: f"{g[0]} {g[1]}", members))
            logging.debug(f"list {group}: called by {source}")
            send_msg(source, f'group {gr[1]} consists of {len(members)} members:\n\n'
                             f'{NEWLINE.join(members_as_strings)}')
        except Exception as e:
            logging.warning(f"list {group}: called by {source}, exception {e}")
            send_msg(source, f"could not list group {group}: {e}")
    elif command == "add":
        try:
            gr = db.group(group_name=group)
            if " " in param:
                split_param = param.split(" ", 1)
                phone = with_country_code(split_param[0])
                name = split_param[1]
            else:
                phone = with_country_code(param)
                name = ""
            db.member_add(group_id=gr[0], member_phone=phone, member_name=name)
            logging.debug(f"add {phone} {name} to group {gr[1]}: called by {source}")
            send_msg(source, f"added {phone} {name} to group {gr[1]}")
        except Exception as e:
            logging.warning(f"add {param} to {group}: called by {source}, exception {e}")
            send_msg(source, f"could not add to group {group}: {e}")
    elif command == "remove":
        try:
            gr = db.group(group_name=group)
            if re.match(r"^[+0-9]{6,}.*$", param):
                phone = with_country_code(param)
                name = ""
                db.member_remove(group_id=gr[0], member_phone=phone)
            else:
                name = param
                phone = ""
                db.member_remove(group_id=gr[0], member_name=name)
            logging.debug(f"remove {phone} {name} from group {gr[1]}: called by {source}")
            send_msg(source, f"deleted {phone} {name} from group {gr[1]} if the person was a member")
        except Exception as e:
            logging.warning(f"remove {param} from {group}: called by {source}, exception {e}")
            send_msg(source, f"could not delete from group {group}: {e}")
    elif command == "send":
        send_success = list()
        send_failure = dict()
        try:
            gr = db.group(group_name=group)
            if param is None or len(param) == 0:
                raise Exception("you didn't supply the message text after the groupname")
            members = db.group_members(group_id=gr[0])
            for member in members:
                try:
                    send_msg(member[0], param)
                    send_success.append(member)
                except Exception as e1:
                    send_failure[member] = e1
            send_success_pretty = NEWLINE.join(list(map(lambda m: f"{m[1]} ({m[0]})",
                                                        send_success)))
            send_failure_pretty = NEWLINE.join(list(map(lambda i: f"{i[0][1]} ({i[0][0]}): {i[1]}",
                                                        send_failure.items())))
            logging.debug(f"sent message to group {group}: called by {source}, message: {param}")
            send_msg(source, f"message to group {group}:\n\n{param}\n\n"
                             f"successfully sent to:\n\n{send_success_pretty}\n\n"
                             f"problems while sending to:\n\n{send_failure_pretty}")
        except Exception as e:
            logging.warning(f"send '{param[:15]}' to group {group}: called by {source}, exception {e}")
            send_msg(source, f"could not send message to group {group}: {e}")
        finally:
            logging.debug(f"send '{param[:15]}' to group {group}: sent successfully to {send_success}")
            logging.debug(f"send '{param[:15]}' to group {group}: failed to send to {send_failure}")


def is_admin_user(number):
    return with_country_code(number) in list(map(with_country_code, config["signal"]["admin_users"].split(" ")))


def reply(timestamp, source, group_id, message, attachments):
    admin_command = bot_administrative_command.match(message)
    basic_command = bot_basic_command.match(message)
    if admin_command is not None and is_admin_user(source):
        execute_admin_cmd(source, admin_command.group(1), admin_command.group(2), admin_command.group(3))
    elif basic_command is not None:
        execute_basic_cmd(source, basic_command.group(1), basic_command.group(2), basic_command.group(3))
    else:
        send_msg(source, config["signal"]["default_message"])


signal.onMessageReceived = reply
try:
    atexit.register(exit_handler)
    loop.run()
finally:
    exit_handler()
