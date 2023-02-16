import json
import os
import re
from datetime import date, datetime, timedelta

import pymongo
from bson import ObjectId

from netboost.settings import BASE_DIR

USER_CONF = {}
if os.path.exists("{}/{}/{}".format(BASE_DIR, "netboost", "conf.py")):
    from netboost.conf import mongo_db_conf

    USER_CONF = mongo_db_conf


class JSONEncoder(json.JSONEncoder):
    """
    用于JSON序列化mongodb中的_id和date对象以及datetime对象
    """

    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        elif isinstance(o, datetime):
            return o.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(o, date):
            return o.strftime('%Y-%m-%d')
        return json.JSONEncoder.default(self, o)


def get_mongo_json_res(data):
    """
    用于将mongo数据进行JSON序列化
    :param data: mongo数据
    :return: JSON数据
    """
    res = JSONEncoder().encode(data)
    return res


mongo_client = pymongo.MongoClient(
    host=USER_CONF.get('host') or '10.254.12.188',
    port=USER_CONF.get('port') or 27017,
    username=USER_CONF.get('username') or "root",
    password=USER_CONF.get('password') or "e1A0Qc4lmU",
    maxPoolSize=1000,
    connect=False)


class MongoOps:
    def __init__(self, db, coll):
        self.db = mongo_client[db]
        self.coll = self.db[coll]

    def remove_collection_content(self):
        """
        清空集合中的内容
        :return:
        """
        self.coll.remove()

    def close_client(self):
        return mongo_client.close()

    def all_table(self):
        return self.db.collection_names()

    def create_index(self, keys, session=None, **kwargs):
        # pymongo.ASCENDING 升序 从小到大
        # pymongo.DESCENDING 降序 从大到小
        """
        my_mongo = MongoOps(db='netops', coll='XunMi')
        my_mongo.create_index([("log_time", pymongo.DESCENDING)])
        my_mongo.create_index("server_ip_address")
        :param keys:
        :param session:
        :param kwargs:
        :return:
        """
        return self.coll.create_index(keys, session=session, **kwargs)

    def list_indexes(self):
        return self.coll.list_indexes()

    def drop_indexes(self):
        return self.coll.drop_indexes()

    def rebuild_index(self, session=None, **kwargs):
        return self.coll.reindex(session=None, **kwargs)

    def drop_index(self, index_or_name, session=None, **kwargs):
        return self.coll.drop_index(index_or_name, session=session, **kwargs)

    def insert_one(self, content):
        """
        将日志写入mongodb(新方法)建议方法合并到insert
        :type content: dict
        :return:
        """
        return self.coll.insert_one(content)

    def insert(self, content):
        """
        :type content: dict
        :return:
        """
        self.coll.insert_one(content)
        return

    def update(self, filter, update):
        """
        将日志写入mongodb
        :type content: dict
        :return:
        result = db.test.update_one({'x': 1}, {'$inc': {'x': 3}})
        res = my_mongo.update(filter=tmp[-1], update={"$set": {'start': int(tmp[-1]['start'])})
        """
        # self.coll.update_one(filter=filter, update=update)
        self.coll.update_many(filter=filter, update=update)
        return

    def advance_update_one(self, **kwargs):
        return self.coll.update_one(**kwargs)

    def update_one(self, filter, update):
        """
        将日志写入mongodb
        :type content: dict
        :return:
        result = db.test.update_one({'x': 1}, {'$inc': {'x': 3}})
        res = my_mongo.update(filter=tmp[-1], update={"$set": {'start': int(tmp[-1]['start']) + 10}})
        """
        result = self.coll.update_one(filter=filter, update=update)
        return result

    def find(self, query_dict=None, fileds=None, sort=None):
        """
        获取所有日志记录
        :param sort:
        :param fileds:
        :param query_dict: 字典形式，比如：{"name": "xxx"}
        example: fileds={'_id': 0, 'node_ip': 1}  只显示node_ip  指定字段
        :type query_dict: dict
        :return: 所有日志记录
        :rtype: list
        """
        if fileds and sort:
            r = self.coll.find(query_dict, fileds).sort(sort, 1)
        elif fileds:
            r = self.coll.find(query_dict, fileds)
        elif query_dict:
            r = self.coll.find(query_dict)
        else:
            r = self.coll.find()
        return list(r)

    def xunmi_find(self, query_dict=None, fileds=None, sort=None):
        """
        获取所有日志记录
        :param sort:
        :param fileds:
        :param query_dict: 字典形式，比如：{"name": "xxx"}
        example: fileds={'_id': 0, 'node_ip': 1}  只显示node_ip  指定字段
        :type query_dict: dict
        :return: 所有日志记录
        :rtype: list
        """
        if fileds and sort:
            r = self.coll.find(query_dict, fileds).sort(sort, -1)
        elif fileds:
            r = self.coll.find(query_dict, fileds)
        elif query_dict:
            r = self.coll.find(query_dict)
        else:
            r = self.coll.find()
        return list(r)

    def find_page_query(self, query_dict=None, fileds=None, sort=None, page_size=10, page_num=1):
        """
                获取所有日志记录
                :param sort:
                :param fileds:
                :param query_dict: 字典形式，比如：{"name": "xxx"}
                example: fileds={'_id': 0, 'node_ip': 1}  只显示node_ip  指定字段
                :type query_dict: dict
                :return: 所有日志记录
                :rtype: list
                """
        skip = page_size * (page_num)
        # 字段排序// -1 为倒序，1 为正序
        if fileds and sort:
            r = self.coll.find(query_dict, fileds).sort(sort, -1).limit(page_size).skip(skip)
        elif fileds:
            r = self.coll.find(query_dict, fileds).limit(page_size).skip(skip)
        elif query_dict:
            r = self.coll.find(query_dict).limit(page_size).skip(skip)
        else:
            r = self.coll.find().limit(page_size).skip(skip)
        return list(r)

    def find_re(self, kwargs, fileds=None, sort=None):
        """
        正则匹配  kwargs :{'name': re.compile(e)}
        example: fileds={'_id': 0, 'node_ip': 1}  只显示node_ip
        :return: 所有日志记录
        :rtype: list
        """
        if fileds and sort:
            r = self.coll.find(kwargs, fileds).sort(sort, 1)
        elif fileds:
            r = self.coll.find(kwargs, fileds)
        else:
            r = self.coll.find(kwargs)
        return list(r)

    def delete_single(self, query):
        """
        删除指定日志记录
        :return:
        """
        return self.coll.delete_one(query)

    def delete_one(self, spec_or_id):
        """
        删除指定日志记录
        :return:
        """
        return self.coll.remove(spec_or_id)

    def delete_many(self, query):
        """
        删除所有日志记录
        :return:
        """
        return self.coll.delete_many(query)

    def delete(self, spec_or_id=None):
        """
        删除所有日志记录
        :return:
        """
        if spec_or_id:
            return self.coll.remove(spec_or_id=spec_or_id)
        else:
            return self.coll.remove({})

    def insert_many(self, doc):
        """
        批量插入操作,doc是一个list
        :return:
        """
        return self.coll.insert_many(documents=doc)

    def count_documents(self):
        """
        统计集合中的文档数
        :return:
        """
        return self.coll.count_documents({})

    def group_by(self, group_key):
        # groupby = group_key

        group = {
            '_id': "$%s" % (group_key if group_key else None),
            "part_quantity": {"$sum": 1}
        }

        ret = self.coll.aggregate(
            [
                {'$group': group},
            ]
        )
        # print(ret)
        return ret


# IPAM操作集合
class IpamOps(object):
    def __init__(self):
        pass

    # 获取全网IP数据
    @staticmethod
    def get_total_ip():
        total_ip_mongo = MongoOps(db='Automation', coll='Total_ip_list')
        res = total_ip_mongo.find(fileds={'_id': 0})
        if res:
            return res
        else:
            return False

    # IPAM成功IP单条数据落库专用
    @staticmethod
    def post_success_ip(ip):
        """
        1、查询除log_time字段外，是否有完全匹配，如果有就只更新log_time字段, 如果log_time字段一致，则不进行任何操作
        2、如果查询不到数据，则新增该字段
        """
        log_time = datetime.now().strftime("%Y-%m-%d")
        my_mongo = MongoOps(db='IPAMData', coll='netaxe_ipam_success_ip')
        query_tmp = my_mongo.find(query_dict={'success_ip': ip})
        # print(query_tmp)
        if query_tmp:
            if query_tmp[0]['log_time'] != log_time:
                return 'update', my_mongo.update(filter={'success_ip': ip}, update={"$set": {'log_time': log_time}})
            else:
                return 'equal no ops', None
        else:
            tmp = {}
            tmp['log_time'] = log_time
            tmp['success_ip'] = ip
            return 'insert', my_mongo.insert(tmp)


    # IPAM成功IP(list格式)批量写入
    @staticmethod
    def post_success_ip_bulk(success_ip_doc):
        format_doc = []
        for data in success_ip_doc:
            tmp = {}
            tmp['log_time'] = datetime.now().strftime("%Y-%m-%d")
            tmp['success_ip'] = data
            format_doc.append(tmp)

        my_mongo = MongoOps(db='IPAMData', coll='netaxe_ipam_success_ip')
        if len(format_doc) >= 1000:
            my_mongo.delete()
            my_mongo.insert_many(format_doc)
        doc_num = my_mongo.count_documents()

        return doc_num

    # IPAM失败IP单条数据落库专用
    @staticmethod
    def post_fail_ip(ip):
        """
        1、查询除log_time字段外，是否有完全匹配，如果有就只更新log_time字段, 如果log_time字段一致，则不进行任何操作
        2、如果查询不到数据，则新增该字段
        """
        log_time = datetime.now().strftime("%Y-%m-%d")
        my_mongo = MongoOps(db='IPAMData', coll='netaxe_ipam_fail_ip')
        query_tmp = my_mongo.find(query_dict={'fail_ip': ip})
        print(query_tmp)
        if query_tmp:
            if query_tmp[0]['log_time'] != log_time:
                return 'update', my_mongo.update(filter={'fail_ip': ip}, update={"$set": {'log_time': log_time}})
            else:
                return 'equal no ops', None
        else:
            tmp = {}
            tmp['log_time'] = log_time
            tmp['fail_ip'] = ip
            return 'insert', my_mongo.insert(tmp)

    # IPAM失败IP(list格式)批量写入
    @staticmethod
    def post_fail_ip_bulk(fail_ip_doc):
        format_doc = []
        for data in fail_ip_doc:
            tmp = {}
            tmp['log_time'] = datetime.now().strftime("%Y-%m-%d")
            tmp['success_ip'] = data
            format_doc.append(tmp)

        my_mongo = MongoOps(db='IPAMData', coll='ipam_fail_ip')
        my_mongo.delete()
        my_mongo.insert_many(format_doc)
        doc_num = my_mongo.count_documents()

        return doc_num

    # IPAM更新IP单条数据落库专用
    @staticmethod
    def post_update_ip(ip):
        """
        1、查询除log_time字段外，是否有完全匹配，如果有就只更新log_time字段, 如果log_time字段一致，则不进行任何操作
        2、如果查询不到数据，则新增该字段
        """
        log_time = datetime.now().strftime("%Y-%m-%d")
        my_mongo = MongoOps(db='IPAMData', coll='netaxe_ipam_update_ip')
        query_tmp = my_mongo.find(query_dict={'update_ip': ip})
        print(query_tmp)
        if query_tmp:
            if query_tmp[0]['log_time'] != log_time:
                return 'update', my_mongo.update(filter={'update_ip': ip}, update={"$set": {'log_time': log_time}})
            else:
                return 'equal no ops', None
        else:
            tmp = {}
            tmp['log_time'] = log_time
            tmp['update_ip'] = ip
            return 'insert', my_mongo.insert(tmp)

    # IPAM批量读取coll内容，比如netaxe_ipam_success_ip、netaxe_ipam_fail_ip
    @staticmethod
    def get_bulk(coll):
        my_mongo = MongoOps(db='IPAMData', coll=coll)
        res = my_mongo.find(fileds={'_id': 0})
        if res:
            return res
        else:
            return False

    # 获取指定coll的数据总数
    @staticmethod
    def get_coll_account(coll):
        my_mongo = MongoOps(db='IPAMData', coll=coll)
        doc_num = my_mongo.count_documents()
        return doc_num

    # 删除指定coll的所有数据
    @staticmethod
    def delet_coll(coll):
        my_mongo = MongoOps(db='IPAMData', coll=coll)
        my_mongo.delete()

        return
