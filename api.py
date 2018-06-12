import json
from flask_sqlalchemy import SQLAlchemy
from flask import jsonify
from flask import Flask
from werkzeug.routing import BaseConverter
from flask_msearch import Search


api = Flask(__name__)
api.config['JSON_AS_ASCII'] = False
api.config['SQLALCHERY_DATABASE_URL'] = "jdbc:sqlserver://sa:sa@192.168.2.135\sql2008:1433;database=HotelSpider"
api.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
api.config['SQLALCHEMY_ECHO'] = True


db = SQLAlchemy(api)

search = Search(db=db)
search.init_app(api)
MSEARCH_INDEX_NAME = 'whoosh_index'

# simple,whoosh

MSEARCH_BACKEND = 'whoosh'

# 自动生成或更新索引

MSEARCH_ENABLE = True

class Hotel(db.Model):

    __tablename__ = 'hotel'

    __searchable__ = ['Name']
    Id = db.Column(db.INTEGER,primary_key=True)
    HId = db.Column(db.String(50),index=True)
    Name = db.Column(db.String(100),index=True)
    City = db.Column(db.String(50))





# 定义正则类，需要继承自BaseConverter
class Regex_url(BaseConverter):
    def __init__(self, url_map, *args):
        super(Regex_url, self).__init__(url_map)
        self.regex = args[0]  # 将正则式赋给regex属性
api.url_map.converters['re'] = Regex_url

@api.route("/get/<re(r'.*'):string>")
def get_hotel_list(string):
    city,Hname = string.split("/")

    ret = Hotel.query.msearch(Hname,fields=["Name"],limit=20).filter(Hotel.City == city).all()
    print(ret)
    return "OK"


@api.route("/get/<re(r'.*'):HId>")
def get_hotel_detail(HId):

    HId = str(HId).replace("'",'').replace(" ",'')

    ret = db.select_hotel(HId)
    if ret is None:
        return jsonify(errmsg="您的输入有误")
    print(ret)
    return jsonify(Source=1,HId=HId)




if __name__ == '__main__':
    api.run()




