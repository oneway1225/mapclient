"""
MAP Client, a program to generate detailed musculoskeletal models for OpenSim.
    Copyright (C) 2012  University of Auckland

This file is part of MAP Client. (http://launchpad.net/mapclient)

    MAP Client is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    MAP Client is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with MAP Client.  If not, see <http://www.gnu.org/licenses/>..
"""
import os
import sys

import psutil
from filelock import FileLock

from PySide2 import QtCore

from mapclient.core.exitcodes import LOG_FILE_LOCK_FAILED
from mapclient.settings.definitions import INTERNAL_WORKFLOWS_DIR

from mapclient.settings.info import VERSION_STRING


def get_data_directory():
    """
    Return the directory where we can store data for the application.
    Like settings and log files etc.
    """
    settings = QtCore.QSettings()
    fn = settings.fileName()

    return os.path.dirname(fn)


def _get_app_directory(name):
    app_dir = get_data_directory()
    name_dir = os.path.join(app_dir, name)

    if not os.path.exists(name_dir):
        os.makedirs(name_dir)

    return name_dir


def get_virtualenv_directory():
    return _get_app_directory('venv_' + VERSION_STRING)


def get_default_internal_workflow_dir():
    return _get_app_directory(INTERNAL_WORKFLOWS_DIR)


def get_virtualenv_site_packages_directory(virtualenv_dir):
    print('Confirm path on other OSes, so far only checked on Windows.')
    return os.path.join(virtualenv_dir, 'Lib', 'site-packages')


def get_log_directory():
    return _get_app_directory('logs')


def get_log_location():
    """
    Return the location of the log file that is associated with the current MAP Client instance. If the current instance has not been
    assigned a log file, a new log file will be created and assigned to the current PID.
    """
    log_directory = get_log_directory()
    database_file = os.path.join(get_data_directory(), "pid_database.txt")

    try:
        # If the user experiences a hardware crash during the execution of this block, it is possible that the lockfile will remain
        # possessed by a dead process. If this happens, the user will have to manually delete the lockfile.
        lock = FileLock(database_file + ".lock", 3)
        with lock:
            try:
                with open(database_file, "r") as file:
                    database = file.read().splitlines()
            except IOError:
                database = []

            # Check if the current PID has already been assigned to a log file. If not, assign it to a new log file.
            current_pid = os.getpid()
            index = -1
            for i in range(len(database)):
                if int(database[i]) == current_pid:
                    index = i
                    break
            if index == -1:
                index = assign_log_file(database_file, database, current_pid)

    except TimeoutError:
        sys.exit(LOG_FILE_LOCK_FAILED)

    log_filename = 'logging_record_' + str(index) + '.log'
    logging_file_location = os.path.join(log_directory, log_filename)

    return logging_file_location


def assign_log_file(database_file, database, current_pid):
    unassigned_indices = []
    for i in range(len(database)):
        if database[i] == '':
            unassigned_indices.append(i)
        else:
            pid = int(database[i])
            if not psutil.pid_exists(pid):
                database[i] = ''
                unassigned_indices.append(i)

    while database and database[-1] == '':
        database.pop()

    max_index = len(database)
    unassigned_indices.append(max_index)
    index = min(unassigned_indices)

    if index < max_index:
        database[index] = current_pid
    else:
        database.append(current_pid)

    with open(database_file, "w") as file:
        for item in database:
            file.write(f"{item}\n")

    return index


def get_configuration_suffix():
    return '.conf'


def get_configuration_file(location, identifier):
    if 'src/mapclient' in location:
        raise Exception('Saving this in the wrong place.')

    return os.path.join(location, identifier + get_configuration_suffix())


DISPLAY_FULL_PATH = 'AIJDKUUGCNEGELND'


def get_configuration(option):
    if option == DISPLAY_FULL_PATH:
        return False


