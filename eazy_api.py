import json

from flask_sqlalchemy import SQLAlchemy
from flask import jsonify
from flask import Flask
from werkzeug.routing import BaseConverter
# from flask_msearch import Search
from db import DbServer

api = Flask(__name__)
api.config['JSON_AS_ASCII'] = False
#
# search = Search()
# search.init_app(api)

db = DbServer()


# 定义正则类，需要继承自BaseConverter
class Regex_url(BaseConverter):
    def __init__(self, url_map, *args):
        super(Regex_url, self).__init__(url_map)
        self.regex = args[0]  # 将正则式赋给regex属性
api.url_map.converters['re'] = Regex_url

@api.route("/search/<re(r'.*'):string>",methods=["POST"])
def get_hotel_list(string):
    city,Hname = string.split("/")

    city = str(city).replace("'",'').replace(" ",'')
    Hname = str(Hname).replace("'",'').replace(" ",'')

    city_ret = db.select_city(city)
    if 0 == city_ret:
        print("城市输入错误")
        return jsonify(errmsg="城市输入错误")
    hotel_ret = db.select_table(city,Hname)
    if hotel_ret is None:
        print("酒店输入有误")
        return jsonify(errmsg="酒店名字输入有误")

    hotels_li = []
    for hotel in hotel_ret:
        item = {}
        item['HId'] = hotel[0]
        item['Name'] = hotel[1]
        item['Phone'] = hotel[3]
        item['Cover'] = hotel[4]
        item["Address"] = hotel[2]
        hotels_li.append(item)
    print("获取列表页成功----")
    return jsonify(hotels=hotels_li)
    # response = make_response(jsonify(response=get_articles(ARTICLES_NAME),hotels=hotels_li))
    # response.headers['Access-Control-Allow-Origin'] = '*'
    # response.headers['Access-Control-Allow-Methods'] = 'POST'
    # response.headers['Access-Control-Allow-Headers'] = 'x-requested-with,content-type'
    # return response

@api.route("/get/<re(r'.*'):HId>",methods=["POST"])
def get_hotel_detail(HId):

    HId = str(HId).replace("'",'').replace(" ",'')


    ret = db.select_hotel(HId)
    if ret is None:
        print("输入的hid有误")
        return jsonify(errmsg="您的输入有误")

    source = ret[1] if ret[1] != None else ''
    city = ret[3] if ret[3] != None else ''
    name = ret[4] if ret[4] != None else ''
    Cover = ret[5] if ret[5] != None else ''
    Level = ret[6] if ret[6] != None else ''
    Score = ret[7] if ret[7] != None else ''
    Address = ret[8] if ret[8] != None else ''
    Price = ret[9] if ret[9] != None else ''
    Price = str(Price).replace("Decimal(",'').replace(")",'')
    Phone = ret[10] if ret[10] != None else ''
    KYDate = ret[11] if ret[11] != None else ''
    ZXDate = ret[12] if ret[12] != None else ''
    RoomCount = ret[14] if[14] != None else ''
    Description = ret[15] if ret[15] != None else ''
    Latitude = ret[16] if ret[16] != None else ''
    Longitude =ret[17] if ret[17] != None else ''
    Hurl = ret[18] if ret[18] != None else ''
    Status = ret[19] if ret[19] != None else ''
    update_time = ret[20] if ret[20] != None else ''
    print("获取详情页成功----")
    return jsonify(Source=source, HId=HId, City=city, Name=name, Cover=Cover, Level=Level, Score=Score, Address=Address,
                   Price=Price, Phone=Phone, KYDate=KYDate, Description=Description, Latitude=Latitude, Longitude=Longitude,
                   Url=Hurl, Status=Status,UpdateTime=update_time,ZXDate=ZXDate,RoomCount=RoomCount
                   ),200, {'Content-Type': 'application/json','Access-Control-Allow-Credentials': 'true'}




if __name__ == '__main__':
    api.run(host='0.0.0.0')




