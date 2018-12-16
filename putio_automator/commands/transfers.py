"""
Flask commands for managing transfers on Put.IO.
"""
import json
import os

from flask_script import Command, Manager
from putio_automator import date_handler
from putio_automator.manage import app


manager = Manager(usage='Manage transfers')

@manager.command
def cancel_by_status(statuses):
    "Cancel transfers by status"
    if isinstance(statuses, str):
        statuses = statuses.split(',')

    transfer_ids = []
    for transfer in app.client.Transfer.list():
        if transfer.status in statuses:
            transfer_ids.append(transfer.id)

    if len(transfer_ids):
        app.client.Transfer.cancel_multi(transfer_ids)

@manager.command
def cancel_completed():
    "Cancel completed transfers"
    cancel_by_status('COMPLETED')

@manager.command
def cancel_seeding():
    "Cancel seeding transfers"
    cancel_by_status('SEEDING')

@manager.command
def clean():
    "Clean finished transfers"
    app.client.Transfer.clean()

@manager.command
def groom():
    "Cancel completed and seeding transfers, and clean afterwards"
    seeding = bool(int(os.getenv('GROOM_SEEDING', True)))

    if seeding:
        statuses = ['SEEDING', 'COMPLETED']
    else:
        statuses = ['COMPLETED']

    cancel_by_status(statuses)

    clean()


@manager.command
def swipe():
    "Like groom, but also removes the files"
    seeding = bool(int(os.getenv('GROOM_SEEDING', True)))

    if seeding:
        statuses = ['SEEDING', 'COMPLETED']
    else:
        statuses = ['COMPLETED']

    transfer_ids = []
    file_ids = []
    for transfer in app.client.Transfer.list():
        if transfer.status in statuses:
            transfer_ids.append(transfer.id)
            file_ids.append(transfer.file_id)

    if len(transfer_ids):
        app.client.Transfer.cancel_multi(transfer_ids)
        app.client.File.delete_multi(file_ids, skip_nonexistents=True)

class List(Command):
    "List transfers: Manually create Flask command cos of name clash with list"
    def run(self):
        "List transfers"
        transfers = app.client.Transfer.list()
        print json.dumps([vars(t) for t in transfers], indent=4, default=date_handler)
manager.add_command('list', List())
