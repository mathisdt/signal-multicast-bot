import psycopg2


class Database:
    def __init__(self, config):
        self.connection = psycopg2.connect(host=config["database"]["host"],
                                           port=config["database"]["port"],
                                           user=config["database"]["username"],
                                           password=config["database"]["password"],
                                           database=config["database"]["database"])
        self.cursor = self.connection.cursor()

        self.sql("""CREATE TABLE IF NOT EXISTS groups (
                 id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
                 name varchar(40)
                 )""")
        self.sql("""CREATE TABLE IF NOT EXISTS members (
                 id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
                 group_id integer REFERENCES groups(id),
                 phone varchar(40) NOT NULL CHECK (phone <> ''),
                 name varchar(40)
                 )""")

    def sql(self, sql, *params, many=False, one=False):
        self.cursor.execute(sql, *params)
        if many:
            # list of tuples
            result = self.cursor.fetchall()
        elif one:
            # tuple
            result = self.cursor.fetchone()
        self.connection.commit()
        if many or one:
            return result

    def close(self):
        self.connection.close()

    def group_add(self, group_name):
        existing = self.sql("select count(*) from groups where lower(name)=lower(%s)", (group_name,), one=True)
        if existing is not None and existing[0] > 0:
            raise Exception("group already present")
        self.sql("insert into groups (name) values (%s)", (group_name,))

    def groups(self):
        """index 0 = id,
        index 1 = group name"""
        return self.sql("select id,name from groups", many=True)

    def group_members(self, group_id=None, group_name=None):
        """index 0 = phone number,
        index 1 = name"""
        if group_id is not None:
            return self.sql("select phone,name from members where group_id=%s", (group_id,), many=True)
        elif group_name is not None:
            return self.sql("select phone,name from members where group_id="
                            "(select id from groups where lower(name)=lower(%s))", (group_name,), many=True)
        else:
            raise Exception("no group identifier given")

    def group(self, group_id=None, group_name=None):
        """index 0 = id,
        index 1 = group name"""
        if group_id is not None:
            result = self.sql("select id,name from groups where id=%s", (group_id,), many=True)
        elif group_name is not None:
            result = self.sql("select id,name from groups where lower(name)=lower(%s)", (group_name,), many=True)
        else:
            raise Exception("no group identifier given")

        if result is None or len(result) != 1:
            raise Exception("no group or multiple groups found")
        return result[0]

    def group_remove(self, group_id=None, group_name=None):
        group = self.group(group_id=group_id, group_name=group_name)
        group_members = self.group_members(group_id=group[0])
        if group_members is None:
            raise Exception("group members not found")
        for group_member in group_members:
            self.member_remove(group_id=group[0], member_phone=group_member[0])
        self.sql("delete from groups where id=%s", (group[0],))

    def member_add(self, group_id=None, group_name=None, member_phone=None, member_name=None):
        if member_phone is None:
            raise Exception("no phone number given")
        group = self.group(group_id=group_id, group_name=group_name)
        if member_name is not None and len(member_name) > 0:
            member = self.sql("select phone,name from members where group_id=%s and lower(name)=lower(%s)",
                              (group[0], member_name), many=True)
            if member is not None and len(member) > 0:
                raise Exception("name is already in group")
        if member_phone is not None:
            member = self.sql("select phone,name from members where group_id=%s and phone=%s",
                              (group[0], member_phone), many=True)
            if member is not None and len(member) > 0:
                raise Exception("phone number is already in group")
        self.sql("insert into members (group_id,phone,name) values (%s, %s, %s)",
                 (group[0], member_phone, member_name))

    def member_remove(self, group_id=None, group_name=None, member_phone=None, member_name=None):
        group = self.group(group_id=group_id, group_name=group_name)
        if member_name is not None:
            member = self.sql("select phone,name from members where group_id=%s and lower(name)=lower(%s)",
                              (group[0], member_name), many=True)
            if member is not None and len(member) > 0:
                self.sql("delete from members where group_id=%s and lower(name)=lower(%s)",
                         (group[0], member_name))
        elif member_phone is not None:
            member = self.sql("select phone,name from members where group_id=%s and phone=%s",
                              (group[0], member_phone), many=True)
            if member is not None and len(member) > 0:
                self.sql("delete from members where group_id=%s and phone=%s",
                         (group[0], member_phone))
        else:
            raise Exception("group member not found")
