import datetime
import postgresql
import config
import threading
import sql_scripts

class Postgres(object):
    __lock = threading.Lock()
    __instance = None
    
    @classmethod
    def get_instance(cls):
        if not cls.__instance:
            with cls.__lock:
                if not cls.__instance:
                    cls.__instance = Postgres()
        return cls.__instance

    def __init__(self):
        self.__instance = postgresql.open(config.db_credentials)
        print('init Postgres' + str(self.__instance))
    def __del__(self):
        if self.__instance:
            print('close Postgres')

    def log(self, user_id, message):
        ins = self.__instance.prepar(
            """
            INSERT INTO users_log (user_id, message, date) 
            SELECT $1, $2, CURRENT_TIMESTAMP;
            """)
        ins(str(user_id), str(message))

    def getTodayUsage(self):
        select = self.__instance.query(
            """
            SELECT COUNT(*) usage_stat FROM users_log u WHERE date_trunc('day', u.date) = date_trunc('day',CURRENT_TIMESTAMP);
            """
        )
        return str(int(select[0]['usage_stat']))
    
    def getWeekUsage(self):
        select = self.__instance.query(
            """
            SELECT COUNT(*) usage_stat FROM users_log WHERE date_trunc('week',date) = date_trunc('week',CURRENT_TIMESTAMP);
            """
        )
        return str(int(select[0]['usage_stat']))
    
    def getMonthUsage(self):
        select = self.__instance.query(
            """
            SELECT COUNT(*) usage_stat FROM users_log WHERE date_trunc('month',date) = date_trunc('month',CURRENT_TIMESTAMP);
            """
        )
        return str(int(select[0]['usage_stat']))
    
    def getUsage(self):
        select = self.__instance.query(
            """
            SELECT COUNT(*) usage_stat FROM users_log;
            """
        )
        return str(int(select[0]['usage_stat']))

    def drop_users(self):
        self.__instance.execute('DROP TABLE users;')

    def getUsersCount(self):
        select = self.__instance.query(
            """
            SELECT COUNT(*) users_count FROM USERS;
            """
        )
        return select[0]

    def init_db(self):
        for script in sql_scripts.init_scripts:
            print(script)
            self.__instance.execute(script)
        
    def add_user(self, user_id, group_id=''):
        ins = self.__instance.prepare(
            """
            INSERT INTO users (user_id, group_id)
            select $1, $2;
            """)
        ins(str(user_id), str(group_id))

    def get_user(self, user_id):
        select = self.__instance.query(
            """
            SELECT user_id
            FROM users
            WHERE user_id = '{0}'
            """.format( str(user_id) ) )
        return select

    def update_user(self, user_id, group_id):
        ins = self.__instance.prepare(
            """
            UPDATE users
            SET group_id = $1
            WHERE user_id = $2;
            """)
        ins(str(group_id), str(user_id))

    def get_user_faculty(self, user_id):
        select = self.__instance.query(
            """
            select faculty from users where user_id = '{0}';
            """.format( str(user_id) )
        )
        return select

    def update_user_faculty(self, user_id, faculty):
        ins = self.__instance.prepare(
            """
            UPDATE users
            SET faculty = $1
            WHERE user_id = $2;
            """)
        ins(str(faculty), str(user_id))
        
    def get_groups_by_faculty(self, faculty):
        select = self.__instance.query(
            """
            SELECT group_id
            FROM schedule WHERE faculty = '{0}'
            ORDER BY group_id;
            """.format( str(faculty) ) )
        return select
    
    def get_group_list(self):
        select = self.__instance.query(
            """
            SELECT DISTINCT group_id
            FROM schedule;
            """)
        return select
    
    def get_faculties(self):
        select = self.__instance.query(
            """
            SELECT distinct faculty
            FROM schedule;
            """)
        return select

    def get_schedule(self, user_id):
        return self.__instance.query(
            """
            SELECT s.schedule
            FROM schedule s
            JOIN users u on u.group_id = s.group_id
            WHERE u.user_id = '{0}'
            """.format( str(user_id) ) )

    
    def get_schedule_by_group(self, group_id):
        return self.__instance.query(
            """
            SELECT s.schedule
            FROM schedule s
            WHERE s.group_id = '{0}'
            """.format( str(group_id) ) )

    def set_schedule(self, group_id, schedule, faculty):
        if len(self.get_schedule_by_group(group_id)) > 0:
            print('len > 0')
            print(group_id)
            print(schedule)
            update = self.__instance.prepare(
                """
                UPDATE schedule
                SET schedule = $1
                WHERE group_id = $2 AND faculty = $3;
                """)
            update(str(schedule), str(group_id), str(faculty))
        else:
            ins = self.__instance.prepare(
                """
                INSERT INTO schedule
                (group_id, schedule, faculty)
                SELECT $1, $2, $3;
                """)
            ins(str(group_id), str(schedule), str(faculty))

    def drop_schedule(self):
        print('deleting all schedule...')
        self.__instance.query(
            """
                DELETE FROM schedule WHERE 1=1;
            """)

    def get_groups(self):
        return self.__instance.query(
            """
            SELECT group_id FROM schedule;
            """)

    
    def get_all_users(self):
        select = self.__instance.query('SELECT * FROM users;')
        return select
    
    def log(self, user_id, message):
        ins = self.__instance.prepare(
            """
            INSERT INTO users_log
            (user_id, message, date)
            SELECT $1, $2, current_timestamp;
            """)
        ins(str(user_id), str(message))
