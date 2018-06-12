import json
import re

import requests
from flask import jsonify, request
from flask import Flask
from werkzeug.routing import BaseConverter
# from flask_msearch import Search
from db import DbServer

api = Flask(__name__)
api.config['JSON_AS_ASCII'] = False

# 定义正则类，需要继承自BaseConverter
class Regex_url(BaseConverter):
    def __init__(self, url_map, *args):
        super(Regex_url, self).__init__(url_map)
        self.regex = args[0]  # 将正则式赋给regex属性
api.url_map.converters['re'] = Regex_url

hotel_list_url = "http://m.elong.com/hotel/api/list?_rt=1527472905302&indate={Indate}&t=1527472904279&outdate={Outdate}&city={cityId}&pageindex={page}&actionName=h5%3D%3Ebrand%3D%3EgetHotelList&ctripToken=&elongToken=dc8bc8aa-b5cb-4cc0-a09e-4291a67df718&esdnum=9168910"
hotel_detail_url = "http://m.elong.com/hotel/api/hoteldetailroomlist?_rt=1527476977933&hotelid={HId}&indate={Indate}&outdate={Outdate}&actionName=h5%3D%3Ebrand%3D%3EgetHotelDetail&ctripToken=&elongToken=dc8bc8aa-b5cb-4cc0-a09e-4291a67df718&esdnum=7556144"
search_url = "http://m.elong.com/hotel/api/list?_rt=1528793341562&pageindex={page}&indate={Indate}&outdate={Outdate}&actionName=h5=>brand=>getHotelList&ctripToken=&elongToken=dc8bc8aa-b5cb-4cc0-a09e-4291a67df718&esdnum=7776463&keywords={keywords}&city={cityId}"

list_headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Referer': 'http://m.elong.com/hotel',
    'User-Agent':'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1'
}


@api.route("/search_list",methods=["GET"])
def search_list():
    city_id = request.args.get("city")
    in_date = request.args.get("indate")
    out_date = request.args.get("outdate")
    pageindex = request.args.get("page")


    if None in (city_id,in_date,out_date,pageindex):
        return jsonify(error="参数不完整")

    if len(in_date) != 10 or len(out_date) != 10:
        return jsonify(error="参数格式不正确")

    try:
        pageindex = int(pageindex)
    except Exception as e:
        return jsonify(error="参数错误")

    response = requests.request("get",hotel_list_url.format(Indate=in_date,Outdate=out_date,cityId=city_id,page=pageindex),headers=list_headers)
    if response.status_code != 200:
        return jsonify(error="网络异常,请重新尝试")

    html_str = response.content.decode()
    html_json = json.loads(html_str)

    hotels_list = html_json["hotelList"]
    # 方案1
    """
    if hotels_list:
        hotel_list = []
        for hotel in hotels_list:
            item = {}
            item["Source"] = "3"
            item["Latitude"] = hotel["baiduLatitude"]
            item["Longitude"] = hotel["baiduLongitude"]
            item["Score"] = hotel["commentScore"]
            item["Url"] = hotel["detailPageUrl"]
            item["Hname"] = hotel["hotelName"]
            item["index_price"] = hotel["lowestPrice"]
            item["Cover"] = hotel["picUrl"]
            item["Level"] = hotel["starLevel"]
            item["HId"] = re.findall(r'http://m.elong.com/hotel/(\d+)/', item["Url"])[0]
            # 请求页面上的一些数据
            headers_hotel = {
                "Referer": "http://m.elong.com/hotel/?city=2003&indate=2018-05-28&outdate=2018-05-29",
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1"
            }
            other_url = "http://m.elong.com/hotel/{HId}/".format(HId=item["HId"])
            response_other = requests.get(other_url, headers=headers_hotel)
            item["Address"] = re.findall(r'<div class="addr">(.*?)</div>', response_other.content.decode())[
                0] if re.findall(r'<div class="addr">(.*?)</div>', response_other.content.decode()) != [] else ''
            item["HTel"] = re.findall(r"hotelTel : '(.*?)'", response_other.content.decode())[0] if re.findall(
                r"hotelTel : '(.*?)'", response_other.content.decode()) != [] else ''
            item["Description"] = re.findall(r'"featureInfo":"(.*?)"', response_other.content.decode())[
                0] if re.findall(r'"featureInfo":"(.*?)"', response_other.content.decode()) != [] else ''
            item["Facilities"] = re.findall(r'"generalAmenities":"(.*?)"', response_other.content.decode())[
                0] if re.findall(r'"generalAmenities":"(.*?)"', response_other.content.decode()) != [] else ''
            item["City"] = re.findall(r'province=;city=(.*?);', response_other.content.decode())[0] if re.findall(
                r'province=;city=(.*?);', response_other.content.decode()) != [] else ''
            item["KYdate"] = re.findall(r'<dd>酒店开业时间 (.*?)年 </dd>', response_other.content.decode())[0] if re.findall(
                r'<dd>酒店开业时间 (.*?)年 </dd>', response_other.content.decode()) != [] else ''
            item["ZXdate"] = item["KYdate"]
            hotel_list.append(item)
        return jsonify(hotel_list=hotel_list)
    """
    # 方案2
    for hotel in hotels_list:
        hotel["HId"] = re.findall(r'http://m.elong.com/hotel/(\d+)/', hotel["detailPageUrl"])[0]

    return jsonify(hotels_list=hotels_list)


@api.route("/search_detail",methods=["GET"])
def search_detail():
    HId = request.args.get("HId")
    in_date = request.args.get("indate")
    out_date = request.args.get("outdate")

    if None in (HId,in_date,out_date):
        return jsonify(error="参数不完整")

    if len(in_date) != 10 or len(out_date) != 10:
        return jsonify(error="参数格式不正确")

    detail_headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Referer': "http://m.elong.com/hotel/{HId}/".format(HId=HId),
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1'
    }

    response = requests.get(hotel_detail_url.format(HId=HId,Indate=in_date,Outdate=out_date),headers=detail_headers)
    # if response.status_code != "200":
    #     return jsonify(error="网络链接错误,请重新尝试")

    html_str = response.content.decode()
    html_json = json.loads(html_str)
    room_list = html_json["roomInfoList"]
    # 方案1
    #return jsonify(room_list=room_list)

    # 方案2
    if room_list:
        rooms_list = []
        for room in room_list:
            Room = {}
            Room["RId"] = room["roomId"]
            Room["RId"] = str(HId) + str(Room["RId"])
            Room["Rname"] = room["roomInfoName"]
            Room["Rarea"] = room["area"]
            Room["Rbed"] = room["bed"]
            Room["Cover"] = room["coverImageUrl"]
            Room["images"] = room["imageList"]
            Room["price"] = room["minAveragePriceSubTotal"]
            # 一些必要的信息
            Room["room"] = []
            for rprice in room["rpList"]:

                Ptype = {}
                addinfo = rprice["additionInfoList"]

                Ptype["People"] = 0
                Ptype["floor"] = ''
                for info in addinfo:
                    if "floor" in str(info) or 'desp: "楼层"' in str(info):
                        Ptype["floor"] = info.get("content")
                    if "psnnum" in str(info) or "可入住人数" in str(info):
                        Ptype["People"] = info.get("content")
                    if "breakfast" in str(info) or 'desp: "早餐"' in str(info):
                        Ptype["breakfast"] = info.get("content")
                Ptype["PId"] = rprice["ratePlanId"]
                Ptype["PId"] = str(Room["RId"]) + str(Ptype["PId"])
                Ptype["rule"] = rprice["cancelTag"]
                Ptype["price"] = rprice["averagePriceSubTotal"]
                Ptype["Pname"] = rprice["productName"]
                Ptype["Pname"] = Room["Rname"] + Ptype["Pname"]
                Room["room"].append(Ptype)
            rooms_list.append(Room)
        return jsonify(room_list=rooms_list)


@api.route("/search_hotel",methods=["GET"])
def search_hotel():
    page = request.args.get("page",0)
    in_date = request.args.get("indate")
    out_date = request.args.get("outdate")
    cityId = request.args.get("city")
    keywords = request.args.get("keywords")

    keywords = keywords.replace(" ","").replace("'","").replace("/",'')

    if None in (in_date,out_date,cityId):
        return jsonify(error="参数不完整")

    if len(in_date) != 10 or len(out_date) != 10:
        return jsonify(error="参数格式不正确")

    response = requests.get(search_url.format(page=page,Indate=in_date,Outdate=out_date,keywords=keywords,cityId=cityId),headers=list_headers)
    if response.status_code != 200:
        return jsonify(error="网络异常，请重新尝试")
    html_str = response.content.decode()
    html_json = json.loads(html_str)
    hotels_list = html_json["hotelList"]
    if not hotels_list:
        return jsonify(error="没有找到符合的酒店")
    for hotel in hotels_list:
        hotel["HId"] = re.findall(r'http://m.elong.com/hotel/(\d+)/', hotel["detailPageUrl"])[0]
    return jsonify(hotels_list=hotels_list)



if __name__ == '__main__':
    api.run(host='0.0.0.0')

