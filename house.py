import logging

from wsgi import jsonify, json, request, session, g

from ihome_main import redis_store, constants, db
from ihome_main.api_1_0 import api
from ihome_main.models import Area, House, Facility, HouseImage
from ihome_main.utils.commons import login_required
from ihome_main.utils.image_storage import storage
from ihome_main.utils.response_code import RET


@api.route('/areas',methods=['GET'])
@login_required
def get_areas_info():
    try:
        areas = redis_store.get('area_info').decode('utf-8')
    except Exception as e:
        logging.error(e)
        areas = None

    #判断areas ,如果不为空, 则直接返回
    if areas != '[]':
        logging.debug('get redis area info')
        return '{"errno":"0","errmsg":"OK","data":%s}' %areas

    try:
        areas = Area.query.all()
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR,errmsg='获取地区信息失败')

    areas_list = []

    for area in areas:
        areas_list.append(area.to_dict())

    json_areas = json.dumps(areas_list)
    try:
        redis_store.setex('area_info',constants.AREA_INFO_EXPIRES,json_areas)
    except Exception as e:
        logging.error(e)

    resp = '{"errno":"0","errmsg":"OK","data":%s}' %json_areas
    return resp


@api.route('/houses',methods=['POST'])
@login_required
def save_new_house():

    req_data = request.get_data().decode('utf-8')
    if not req_data:
        return jsonify(errno=RET.PARAMERR,errmsg='参数缺失')

    dict_data = json.loads(req_data)

    title = dict_data.get('title')
    price = dict_data.get('price')
    area_id = dict_data.get('area_id')
    address = dict_data.get('address')
    room_count = dict_data.get('room_count')
    acreage = dict_data.get('acreage')
    unit = dict_data.get('unit')
    capacity = dict_data.get('capacity')
    beds = dict_data.get('beds')
    deposit = dict_data.get('deposit')
    min_days = dict_data.get('min_days')
    max_days = dict_data.get('max_days')


    if not all([title,price,area_id,address,room_count,acreage,unit,capacity,beds,deposit,min_days,max_days]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数缺失')

    try:
        price = int(float(price)*100)
        deposit = int(float(deposit)*100)
    except Exception as e:
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误')

    house = House()
    house.user_id = session.get('user_id')
    house.area_id = area_id
    house.title = title
    house.price = price
    house.address = address
    house.room_count = room_count
    house.acreage = acreage
    house.unit = unit
    house.capacity = capacity
    house.beds = beds
    house.deposit = deposit
    house.min_days = min_days
    house.max_days = max_days

    facility = dict_data.get('facility')
    if facility:
        facilities = Facility.query.filter(Facility.id.in_(facility)).all()
        house.facilities = facilities

    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='保存房屋信息失败')

    return jsonify(errno=RET.OK,errmsg='ok',data={'house_id':house.id})


@api.route('/houses/<int:house_id>/images',methods=['POST'])
@login_required
def save_house_image(house_id):
    image = request.files.get('house_image')

    if not image:
        return jsonify(errno=RET.PARAMERR,errmsg='未上传图片')

    try:
        house = House.query.get(house_id)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DATAERR,errmsg='房屋不存在')

    image_data = image.read()

    try:
        image_name = storage(image_data)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.THIRDERR,errmsg='上传图片失败')

    house_iamge = HouseImage()

    house_iamge.house_id = house_id
    house_iamge.url = image_name
    db.session.add(house_iamge)

    try:
        db.session.commit()
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='保存房屋图片失败')

    image_url = constants.QINIU_DOMIN_PREFIX + image_name
    return jsonify(errno=RET.OK,errmsg='OK',data={'url':image_url})


@api.route('/houses/<int:house_id>',methods=['GET'])
def get_house_detail(house_id):

    user_id = session.get('user_id')

    if not house_id:
        return jsonify(errno=RET.PARAMERR,errmsg='参数缺失')

    try:
        ret = redis_store.get('house_info_%s' % house_id).decode('utf-8')
    except Exception as e:
        logging.error(e)
        ret = None

    if ret:
        logging.debug('get house_info from redis')
        return jsonify(errno=RET.OK,errmsg='OK',data={'user_id':user_id,'house':ret})

    try:
        house = House.query.get(house_id)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询数据库失败')

    if not house:
        return jsonify(errno=RET.NODATA,errmsg='房屋不存在')

    try:
        house_data = house.to_full_dict()
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DATAERR,errmsg='数据出错')

    house_json = json.dumps(house_data)
    try:
        redis_store.setex('house_info_%s'%house_id,constants.HOUSE_DETAIL_EXPIRES,house_json)
    except Exception as e:
        logging.error(e)

    resp = '{"errno":"0","errmsg":"OK","data":{"user_id":%s,"house":%s}}' %(user_id,house_json)
    return resp

