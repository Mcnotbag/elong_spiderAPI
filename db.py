import pymssql

#创建student表
# Student = '''
#     create table Student(
#         StdID int primary key not null,
#         StdName varchar(100) not null,
#         Gender enum('M','F') not null,
#         Age int
#     )
# '''



class DbServer(object):
    def __init__(self):
        self.conn =pymssql.connect(host='192.168.2.135\sql2008', user='sa', password='sa', database='HotelSpider')
        self.cur = self.conn.cursor()

    def __del__(self):
        self.cur.close()
        self.conn.close()

    def create_table(self):

        sql = """
            create table Hotels(
            Source int,
            Hid varchar(100) unique,
            City varchar(100),
            Name varchar(100),
            Cover varchar(100),
            Level varchar(100),
            Score real,
            Address varchar(200),
            Price Decimal(8,2),
            Phone varchar(20),
            KYDate varchar(20),
            Latitude real,
            Longitude real,
            Url varchar(200),
            Description varchar(500)
            )
        """
        try:
            self.cur.execute(sql)
            print("插入成功")
        except Exception as e:
            print("插入失败")
            print(e)
        self.conn.commit()

    def select_table(self,city,Hname):
        sql = """
            select HId,Name,Address,Phone,Cover from Hotel where city = '{}' and NAME like '%{}%'
        """.format(city,Hname)
        ret = None
        try:
            self.cur.execute(sql)
            ret = self.cur.fetchall()
            print(ret)
            print(type(ret))
            print("查询成功")
        except Exception as e:
            print("查询失败")
            print(e)
        self.conn.commit()
        if ret:

            return ret
        else:
            return None

    def select_city(self,city):
        print(city)
        sql = """
            select * from Hotel where City='%s'
        """ % city
        ret = None
        try:
            self.cur.execute(sql)
            ret = self.cur.fetchone()
            print("查询成功")
        except Exception as e:
            print("查询失败")
            print(e)
        self.conn.commit()

        if ret:
            return 1
        else:
            return 0

    def select_hotel(self,Hid):
        sql = """
            select * from Hotel where HId='%s'
        """ % Hid
        ret = None
        try:
            self.cur.execute(sql)
            ret = self.cur.fetchone()
            print("查询成功")
        except Exception as e:
            print("查询失败")
            print(e)
        self.conn.commit()

        if ret:
            return ret
        else:
            return None


if __name__ == '__main__':
    db = DbServer()
    db.create_table()