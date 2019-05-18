# Copyright (c) 2016-2019 Renata Hodovan, Akos Kiss.
# Copyright (c) 2019 Tamas Keri.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import time

from datetime import datetime

from bson.objectid import ObjectId
from pymongo import ASCENDING, MongoClient, ReturnDocument


class MongoDriver(object):

    def __init__(self, uri):
        self.uri = uri
        self.session_start = time.time()

    @property
    def _db(self):
        return MongoClient(self.uri).get_database()

    def init_db(self, fuzzers):
        """
        Initializes the 'fuzzinator_issues', 'fuzzinator_stats', and
        'fuzzinator_configs' collections: creates the collections and
        their indexes if they don't exist already. Additionally, it saves
        the subconfigs of the current sut-fuzzer pairs, and zero-initializes
        the exec and issue count statistics of any new sut-fuzzer-subconfigs.
        """
        db = self._db

        issues = db.fuzzinator_issues
        issues.create_index([('sut', ASCENDING), ('id', ASCENDING)])
        issues.create_index([('sut', ASCENDING), ('fuzzer', ASCENDING), ('subconfig', ASCENDING)])
        issues.create_index('first_seen')
        issues.create_index('last_seen')
        issues.create_index('invalid')
        issues.create_index('count')
        issues.create_index('fuzzer')
        issues.create_index('invalid')

        stats = db.fuzzinator_stats
        stats.create_index([('sut', ASCENDING), ('fuzzer', ASCENDING), ('subconfig', ASCENDING)])

        configs = db.fuzzinator_configs
        configs.create_index('subconfig')

        for fuzz_name, fuzz_data in fuzzers.items():
            configs.find_one_and_update(filter={'subconfig': fuzz_data['subconfig']},
                                        update={'$setOnInsert': {'subconfig': fuzz_data['subconfig'], 'src': fuzz_data['src']}},
                                        upsert=True)

            stats.find_one_and_update(filter={'sut': fuzz_data['sut'], 'fuzzer': fuzz_name, 'subconfig': fuzz_data['subconfig']},
                                      update={'$setOnInsert': {'sut': fuzz_data['sut'], 'fuzzer': fuzz_name, 'subconfig': fuzz_data['subconfig'], 'exec': 0, 'crashes': 0}},
                                      upsert=True)

    def add_issue(self, issue):
        # MongoDB assumes that dates and times are in UTC, hence it must
        # be used in the `first_seen` field, too.
        now = datetime.utcnow()
        result = self._db.fuzzinator_issues.find_one_and_update(
            {'sut': issue['sut'], 'id': issue['id'], 'invalid': {'$exists': False}},
            {'$setOnInsert': dict(issue, first_seen=now),
             '$set': dict(last_seen=now),
             '$inc': dict(count=1)},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        issue.update(result)
        # `first_seen` and `last_seen` values cannot be compared to `now` due
        # to some rounding in pymongo, the returning values can be slightly
        # different from the value stored in `now` (on nanosecond level).
        return issue['first_seen'] == issue['last_seen']

    def get_issues(self, filter=None, skip=0, limit=0, sort=None, include_invalid=True, show_all=True, detailed=True):
        filter = filter or {}
        if not show_all:
            filter['first_seen'] = {'$gte': self.session_start}
        if not include_invalid:
            filter['invalid'] = {'$exists': False}

        aggregator = []
        if filter:
            aggregator.append({'$match': filter})
        if sort:
            aggregator.append({'$sort': sort})
        if skip:
            aggregator.append({'$skip': skip})
        if limit:
            aggregator.append({'$limit': limit})
        if not detailed:
            aggregator.append({'$project': {'id': 1, 'sut': 1, 'fuzzer': 1, 'first_seen': 1, 'last_seen': 1, 'count': 1, 'invalid': 1, 'reduced': {'$ifNull': [True, None]}, 'reported': 1}})

        return list(self._db.fuzzinator_issues.aggregate(aggregator))

    def find_issue_by_oid(self, oid):
        return self._db.fuzzinator_issues.find_one({'_id': ObjectId(oid)})

    def find_issues_by_suts(self, suts):
        return list(self._db.fuzzinator_issues.find({'sut': {'$in': suts}}))

    def update_issue_by_oid(self, oid, _set):
        self._db.fuzzinator_issues.update_one({'_id': ObjectId(oid)}, {'$set': _set})

    def remove_issue_by_oid(self, oid):
        self._db.fuzzinator_issues.delete_one({'_id': ObjectId(oid)})

    def find_config_by_id(self, id):
        return self._db.fuzzinator_configs.find_one({'subconfig': id})

    def get_stats(self, filter=None, skip=0, limit=0, sort=None, show_all=True, detailed=True):
        aggregator = [
            # Get an empty document
            {'$limit': 1},  # Note: this works only if fuzzinator_stats has at least one element.
            {'$project': {'_id': 1}},
            {'$project': {'_id': 0}},

            # Get unique crash counts from the issues (exec and crash counts are set to 0).
            {'$lookup': {
                'from': 'fuzzinator_issues',
                'pipeline': ([] if show_all else [
                    {'$match': {'first_seen': {'$gte': self.session_start}}}
                ]) + [
                    {'$group': {
                        '_id': {'sut': '$sut', 'fuzzer': '$fuzzer', 'subconfig': '$subconfig'},
                        'sut': {'$first': '$sut'}, 'fuzzer': {'$first': '$fuzzer'}, 'subconfig': {'$first': '$subconfig'},
                        'exec': {'$sum': 0}, 'crashes': {'$sum': 0}, 'unique': {'$sum': 1},
                    }},
                ],
                'as': 'fuzzinator_issues',
            }},

            # Get exec and crash counts from the stats (unique crash counts are set to 0).
            {'$lookup': {
                'from': 'fuzzinator_stats',
                'pipeline': [
                    {'$addFields': {'subconfig': '$subconfig'}},
                ],
                'as': 'fuzzinator_stats',
            }},

            # Union the two results.
            {'$project': {'union': {'$concatArrays': ['$fuzzinator_issues', '$fuzzinator_stats']}}},
            {'$unwind': '$union'},
            {'$replaceRoot': {'newRoot': '$union'}},

            # Sum the stats and drop all-zeros lines.
            {'$group': {
                '_id': {'sut': '$sut', 'fuzzer': '$fuzzer', 'subconfig': '$subconfig'},
                'sut': {'$first': '$sut'}, 'fuzzer': {'$first': '$fuzzer'}, 'subconfig': {'$first': '$subconfig'},
                'exec': {'$sum': '$exec'}, 'crashes': {'$sum': '$crashes'}, 'unique': {'$sum': '$unique'},
            }},
            {'$match': {'$or': [{'exec': {'$gt': 0}}, {'crashes': {'$gt': 0}}, {'unique': {'$gt': 0}}]}},
        ] + ([] if not detailed else [
            # Extend stats with the ini snippet
            {'$lookup': {
                'from': 'fuzzinator_configs',
                'localField': 'subconfig',
                'foreignField': 'subconfig',
                'as': 'fuzzinator_configs',
            }},
            {'$unwind': {'path': '$fuzzinator_configs', 'preserveNullAndEmptyArrays': True}},
        ]) + [
            # Create a 2-level hierarchy of stats grouped by fuzzer and sut, detailed by config
            {'$group': {
                '_id': {'sut': '$sut', 'fuzzer': '$fuzzer'},
                'sut': {'$first': '$sut'}, 'fuzzer': {'$first': '$fuzzer'},
                'exec': {'$sum': '$exec'}, 'crashes': {'$sum': '$crashes'}, 'unique': {'$sum': '$unique'},
                'configs': {'$push': {'subconfig': '$subconfig', 'src': '$fuzzinator_configs.src',
                                      'exec': '$exec', 'crashes': '$crashes', 'unique': '$unique'}},
            }},
            {'$project': {'_id': 0}},
        ]

        if filter:
            aggregator.append({'$match': filter})
        if sort:
            aggregator.append({'$sort': sort})
        if skip:
            aggregator.append({'$skip': skip})
        if limit:
            aggregator.append({'$limit': limit})

        result = dict()
        for document in self._db.fuzzinator_stats.aggregate(aggregator):
            result[(document['fuzzer'], document['sut'])] = dict(fuzzer=document['fuzzer'],
                                                                 sut=document['sut'],
                                                                 exec=document['exec'],
                                                                 issues=document['crashes'],
                                                                 unique=document['unique'],
                                                                 configs=document['configs'])
        return result

    def update_stat(self, sut, fuzzer, subconfig, batch, issues):
        self._db.fuzzinator_stats.find_one_and_update({'sut': sut, 'fuzzer': fuzzer, 'subconfig': subconfig},
                                                      {'$inc': {'exec': int(batch), 'crashes': issues}},
                                                      upsert=True)
