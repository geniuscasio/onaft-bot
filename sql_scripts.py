# this init scripts can be replaced any time

TABLE_SCHEDULE  = 'schedule'
TABLE_USERS     = 'users'
TABLE_USERS_LOG = 'users_log'

F_USER_ID    = 'user_id'
F_MESSAGE    = 'message'
F_DATE       = 'date'
F_GROUP_NAME = 'group_id'
F_SCHEDULE   = 'schedule'
F_FACULTY    = 'faculty'


CREATE_SCHEDULE = """
        CREATE TABLE IF NOT EXISTS schedule (
        group_id TEXT NOT NULL PRIMARY KEY UNIQUE,
        schedule TEXT,
        faculty TEXT);
    """

CREATE_USERS = """
        CREATE TABLE IF NOT EXISTS users (
        user_id TEXT NOT NULL PRIMARY KEY UNIQUE,
        group_id TEXT,
        faculty TEXT);
    """

CREATE_USERS_LOG = """
        CREATE TABLE IF NOT EXISTS users_log (
        user_id TEXT,
        message TEXT,
        date TIMESTAMP);
    """

init_scripts = [CREATE_SCHEDULE, CREATE_USERS, CREATE_USERS_LOG]

