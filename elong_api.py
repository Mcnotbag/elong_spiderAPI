import json
import re
import string
from urllib import parse

from lxml import etree

import requests
from flask import jsonify, request
from flask import Flask
from werkzeug.routing import BaseConverter
# from flask_msearch import Search
# from db import DbServer

api = Flask(__name__)
api.config['JSON_AS_ASCII'] = False
# db = DbServer()
# 定义正则类，需要继承自BaseConverter
class Regex_url(BaseConverter):
    def __init__(self, url_map, *args):
        super(Regex_url, self).__init__(url_map)
        self.regex = args[0]  # 将正则式赋给regex属性
api.url_map.converters['re'] = Regex_url

hotel_list_url = "http://m.elong.com/hotel/api/list?_rt=1527472905302&indate={Indate}&t=1527472904279&outdate={Outdate}&city={cityId}&pageindex={page}&actionName=h5%3D%3Ebrand%3D%3EgetHotelList&ctripToken=&elongToken=dc8bc8aa-b5cb-4cc0-a09e-4291a67df718&esdnum=9168910"
hotel_detail_url = "http://m.elong.com/hotel/api/hoteldetailroomlist?_rt=1527476977933&hotelid={HId}&indate={Indate}&outdate={Outdate}&actionName=h5%3D%3Ebrand%3D%3EgetHotelDetail&ctripToken=&elongToken=dc8bc8aa-b5cb-4cc0-a09e-4291a67df718&esdnum=7556144"
search_url = "http://m.elong.com/hotel/api/list?_rt=1528793341562&pageindex={page}&indate={Indate}&outdate={Outdate}&actionName=h5=>brand=>getHotelList&ctripToken=&elongToken=dc8bc8aa-b5cb-4cc0-a09e-4291a67df718&esdnum=7776463&keywords={keywords}&city={cityId}"
near_hotel_url = "http://m.elong.com/hotel/api/list?_rt=1529044784907&lbstype=2&indate={Indate}&startlng={lng}&startlat={lat}&outdate={Outdate}&isnear=1&city={cityId}&pageindex={page}&actionName=h5%3D%3Ebrand%3D%3EgetHotelList&ctripToken=&elongToken=&esdnum=7898076"
baidu_search_list_url = "https://map.baidu.com/mobile/webapp/search/search/qt=s&wd={keywords}&c=340&searchFlag=bigBox&version=5&exptype=dep&src_from=webapp_all_bigbox&sug_forward=&src=2/vt=/?pagelets[]=pager&pagelets[]=page_data&t=937717"
baidu_search_detail_url = "https://map.baidu.com/hotel?qt=ota_order_price&from=maponline&t=1528871587017&st={Indate}&et={Outdate}&uid={uid}&v=3.1&expvar=hotel_detail_new&app_from=map&ishour=0&src_from=webapp_all_bigbox&pindex=0&size=20"
baidu_hname_filter_url = "https://map.baidu.com/su?wd={keywords}&callback=suggestion_1528872905826&cid=&b=&pc_ver=2&type=0&newmap=1&ie=utf-8&callback=jsonp3"

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
        # print(hotel["hotelName"])

    return jsonify(hotels_list=hotels_list)


@api.route("/search_detail",methods=["GET"])
def search_detail():
    HId = request.args.get("HId")
    in_date = request.args.get("indate")
    out_date = request.args.get("outdate")
    Hname = request.args.get("name")

    if None in (HId,in_date,out_date,Hname):
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
    try:
        elong_low_price = room_list[0]["minAveragePriceSubTotal"]
    except Exception as e:
        print(e)
        elong_low_price = 0
    baidu_low_price = 0

    # 方案1
    baidu_list_hearders = {
        'User-Agent':'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1',
        'Referer':'https://map.baidu.com/mobile/webapp/index/index/',
        'Host':'map.baidu.com',
        'Accept-Language': 'zh-CN,zh;q=0.9',
    }
    # 搜索文字过滤
    Hname_quete = parse.quote(Hname,safe=string.printable)
    keywords_response = requests.get(baidu_hname_filter_url.format(keywords=Hname_quete),headers=baidu_list_hearders)
    keywords_response_json = json.loads(keywords_response.content.decode()[25:-1]) # 可能会报错
    new_keywords_str = keywords_response_json["s"][0]
    Hname,baidu_uuid = re.findall(r"\w+\$\w+\$\$(.*?)\$\w+\$([0-9a-zA-Z]+)\$\w+\$\w+\$",new_keywords_str)[0]
    # 向百度求情获取酒店列表
    # baidu_list_response = requests.get(baidu_search_list_url.format(keywords=Hname_quete),headers=baidu_list_hearders)
    # baidu_list_html_str = baidu_list_response.content.decode()
    # html = etree.HTML(baidu_list_html_str)
    # baidu_hotel_id_str = html.xpath("//div[@id='fis_elm__6']//ul/li[1]/a/@href")[0]
    # baidu_uuid = re.findall(r"uid=(\w+)&", baidu_hotel_id_str)[0]
    # 获取百度uuid 向百度详情页发出请求
    baidu_detail_response = requests.get(baidu_search_detail_url.format(Indate=in_date,Outdate=out_date,uid=baidu_uuid),headers=baidu_list_hearders)
    baidu_detail_response_json = json.loads(baidu_detail_response.content.decode())
    if baidu_detail_response_json["errorMsg"] == "success":
        baidu_low_price = baidu_detail_response_json["data"]["room_data"][0]["lowest_price"]

    # print(baidu_low_price)
    # print(elong_low_price)
    if int(elong_low_price) <= int(baidu_low_price):
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

                    Room["People"] = 0
                    Room["floor"] = ''
                    for info in addinfo:
                        if "floor" in str(info) or 'desp: "楼层"' in str(info):
                            Room["floor"] = info.get("content")
                        if "psnnum" in str(info) or "可入住人数" in str(info):
                            Room["People"] = info.get("content")
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
    else:
        # rooms_list = baidu_detail_response_json["data"]["room_data"]
        # return jsonify(room_list=rooms_list)
        room_list = baidu_detail_response_json["data"]["room_data"]
        rooms_list = []
        for room in room_list:
            Room = {}
            Room["Rname"] = room["room_type_name"]
            Room["Rarea"] = room["base_info"]["area"] if "area" in str(room["base_info"]) else ''
            Room["Rbed"] = room["base_info"]["bed_type"]
            Room["floor"] = room["base_info"]["floor"] if "floor" in str(room["base_info"]) else ''
            Room["Cover"] = room["base_info"]["images"][0] if room["base_info"]["images"] != [] else ''
            Room["images"] = room["base_info"]["images"]
            Room["price"] = room["lowest_price"]
            Room["room"] = []
            for rprice in room["price_info"]:
                Ptype = {}
                Ptype["rule"] = rprice["cancel_policy"]
                Ptype["Pname"] = rprice["ota_room_name"]
                Ptype["price"] = rprice["actual_price"]
                Ptype["breakfast"] = rprice["breakfast"]
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
        baidu_list_hearders = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1',
            'Referer': 'https://map.baidu.com/mobile/webapp/index/index/',
            'Host': 'map.baidu.com',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }
        keywords = parse.quote(keywords,safe=string.printable)
        keywords_response = requests.get(baidu_hname_filter_url.format(keywords=keywords),
                                         headers=baidu_list_hearders)
        keywords_response_json = json.loads(keywords_response.content.decode()[25:-1])  # 可能会报错
        new_keywords_str = keywords_response_json["s"][0]
        if new_keywords_str[0] == "$":
            new_keywords = re.match(r"\$\$\$(\w+)\$",new_keywords_str).group(1)
            new_keywords = parse.quote(new_keywords,safe=string.printable)
            # 向百度求情获取酒店列表
            baidu_list_response = requests.get(baidu_search_list_url.format(keywords=new_keywords),headers=baidu_list_hearders)
            baidu_list_html_str = baidu_list_response.content.decode()
            # with open("baidu.html","w",encoding="utf-8") as f:
            #     f.write(baidu_list_html_str)
            html = etree.HTML(baidu_list_html_str)
            baidu_hotel_list = html.xpath("//ul[@class='hotel-list ' or @class='place-list ']/li")
            baidu_hotels = []
            for baidu_hotel in baidu_hotel_list:
                item = {}
                data_str = baidu_hotel.xpath("./@data-url")[0] if baidu_hotel.xpath("./@data-url") != [] else baidu_hotel.xpath("./a/@href")[0]
                print(data_str)
                item["Hname"] = re.findall(r"da_adtitle=(.*?)&",data_str)[0]
                item["uuid"] = re.findall(r"uid=(\w+)&",data_str)[0]
                baidu_hotels.append(item)
            return jsonify(errorNO="B",error="未找到符合酒店向百度查找",hotels_list=baidu_hotels)
        else:
            baidu_hotels = []
            item = {}
            item['Hname'], item['uuid'] ,item["city"]= \
            re.findall(r"\w+\$\w+\$\$([\w\(\)]+)\$\w+\$([0-9a-zA-Z]+)\$(\w+)\$\w+\$", new_keywords_str)[0]
            baidu_hotels.append(item)
            return jsonify(errorNO="B",error="未找到符合酒店向百度查询",hotels_list=baidu_hotels)

    for hotel in hotels_list:
        hotel["HId"] = re.findall(r'http://m.elong.com/hotel/(\d+)/', hotel["detailPageUrl"])[0]
    return jsonify(hotels_list=hotels_list)

@api.route("/search_baidudetail",methods=["GET"])
def search_baidudetail():
    # Hname = request.args.get("name")
    uuid = request.args.get("uuid")
    in_date = request.args.get("indate")
    out_date = request.args.get("outdate")

    if None in (in_date,out_date,uuid):
        return jsonify(error="参数不完整")

    if len(in_date) != 10 or len(out_date) != 10:
        return jsonify(error="参数格式不正确")

    # 获取百度uuid 向百度详情页发出请求
    baidu_list_hearders = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1',
        'Referer': 'https://map.baidu.com/mobile/webapp/index/index/',
        'Host': 'map.baidu.com',
        'Accept-Language': 'zh-CN,zh;q=0.9',
    }

    baidu_detail_response = requests.get(
        baidu_search_detail_url.format(Indate=in_date, Outdate=out_date, uid=uuid),
        headers=baidu_list_hearders)
    baidu_detail_response_json = json.loads(baidu_detail_response.content.decode())
    if baidu_detail_response_json["errorMsg"] == "success":
        room_list = baidu_detail_response_json["data"]["room_data"]
        rooms_list = []
        for room in room_list:
            Room = {}
            Room["Rname"] = room["room_type_name"]
            Room["Rarea"] = room["base_info"]["area"] if "area" in str(room["base_info"]) else ''
            Room["Rbed"] = room["base_info"]["bed_type"]
            Room["floor"] = room["base_info"]["floor"] if "floor" in str(room["base_info"]) else ''
            Room["Cover"] = room["base_info"]["images"][0] if room["base_info"]["images"] != [] else ''
            Room["images"] = room["base_info"]["images"]
            Room["price"] = room["lowest_price"]
            Room["room"] = []
            for rprice in room["price_info"]:
                Ptype = {}
                Ptype["rule"] = rprice["cancel_policy"]
                Ptype["Pname"] = rprice["ota_room_name"]
                Ptype["price"] = rprice["actual_price"]
                Ptype["breakfast"] = rprice["breakfast"]
                Room["room"].append(Ptype)
            rooms_list.append(Room)
        return jsonify(room_list=rooms_list)

    else:
        # print(baidu_detail_response_json["errorMsg"])
        return jsonify(error="无合作方酒店数据")


@api.route("/search_near",methods=["GET"])
def search_near():
    in_date = request.args.get("indate")
    out_date = request.args.get("outdate")
    cityId = request.args.get("city",2003)
    lng = request.args.get("lng")
    lat = request.args.get("lat")
    page = request.args.get("page","0")

    if None in (in_date,out_date,lng,lat,page,cityId):
        return jsonify(error="参数不完整")

    if len(in_date) != 10 or len(out_date) != 10:
        return jsonify(error="参数格式不正确")

    try:
        float(lat)
        float(lng)
    except Exception as e:
        return jsonify(error="参数格式不正确")

    response = requests.get(near_hotel_url.format(Indate=in_date,Outdate=out_date,cityId=cityId,page=page,lat=lat,lng=lng))
    if response.status_code != 200:
        return jsonify(error="网络异常,请重新尝试")

    html_str = response.content.decode()
    html_json = json.loads(html_str)

    hotels_list = html_json["hotelList"]
    for hotel in hotels_list:
        hotel["HId"] = re.findall(r'http://m.elong.com/hotel/(\d+)/', hotel["detailPageUrl"])[0]

    return jsonify(hotels_list=hotels_list)




# eazy_api 结合
"""
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



"""

if __name__ == '__main__':
    api.run(host='0.0.0.0')

