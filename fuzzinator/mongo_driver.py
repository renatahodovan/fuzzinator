# Copyright (c) 2016-2019 Renata Hodovan, Akos Kiss.
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

    def init_db(self, sut_fuzzer_pairs):
        """
        Creates a 'fuzzinator_issues' collection with appropriate indexes (if
        not existing already), and initializes a 'fuzzinator_stats' collection
        for (sut, fuzzer) pairs (with 0 exec and issue counts if not existing
        already).
        """
        db = self._db

        issues = db.fuzzinator_issues
        issues.create_index([('sut', ASCENDING), ('id', ASCENDING)])
        issues.create_index([('sut', ASCENDING), ('fuzzer', ASCENDING)])
        issues.create_index('first_seen')
        issues.create_index('invalid')

        stats = db.fuzzinator_stats
        stats.create_index([('sut', ASCENDING), ('fuzzer', ASCENDING)])

        for sut, fuzzer in sut_fuzzer_pairs:
            if stats.find({'sut': sut, 'fuzzer': fuzzer}).count() == 0:
                stats.insert_one({'sut': sut, 'fuzzer': fuzzer, 'exec': 0, 'crashes': 0})

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

    def all_issues(self, include_invalid=False, show_all=True):
        query = {}
        if not show_all:
            query['first_seen'] = {'$gte': self.session_start}
        if not include_invalid:
            query['invalid'] = {'$exists': False}
        return list(self._db.fuzzinator_issues.find(query))

    def find_issue_by_id(self, _id):
        return self._db.fuzzinator_issues.find_one({'_id': ObjectId(_id)})

    def find_issues_by_suts(self, suts):
        return list(self._db.fuzzinator_issues.find({'sut': {'$in': suts}}))

    def update_issue_by_id(self, _id, _set):
        self._db.fuzzinator_issues.update_one({'_id': ObjectId(_id)}, {'$set': _set})

    def remove_issue_by_id(self, _id):
        self._db.fuzzinator_issues.delete_one({'_id': ObjectId(_id)})

    def get_stats(self, filter=None, skip=0, limit=0, sort=None, show_all=True):
        issues_pipeline = []
        if not show_all:
            issues_pipeline.append({'$match': {'first_seen': {'$gte': self.session_start}}})
        issues_pipeline.extend([
            {'$group': {'_id': {'sut': '$sut', 'fuzzer': '$fuzzer'}, 'unique': {'$sum': 1}}},
            {'$addFields': {'sut': '$_id.sut', 'fuzzer': '$_id.fuzzer', 'exec': 0, 'crashes': 0}}
        ])

        aggregator = [
            # Get an empty document
            {'$limit': 1},  # Note: this works only if fuzzinator_stats has at least one element.
            {'$project': {'_id': 1}},
            {'$project': {'_id': 0}},

            # Get unique crash counts from the issues (exec and crash counts are set to 0).
            {'$lookup': {
                'from': 'fuzzinator_issues',
                'pipeline': issues_pipeline,
                'as': 'fuzzinator_issues',
            }},

            # Get exec and crash counts from the stats (unique crash counts are set to 0).
            {'$lookup': {
                'from': 'fuzzinator_stats',
                'pipeline': [
                    {'$addFields': {'unique': 0}},
                ],
                'as': 'fuzzinator_stats',
            }},

            # Union the two results.
            {'$project': {'union': {'$concatArrays': ['$fuzzinator_issues', '$fuzzinator_stats']}}},
            {'$unwind': '$union'},
            {'$replaceRoot': {'newRoot': '$union'}},

            # Sum the stats and drop all-zeros lines.
            {'$group': {'_id': {'sut': '$sut', 'fuzzer': '$fuzzer'}, 'exec': {'$sum': '$exec'}, 'crashes': {'$sum': '$crashes'}, 'unique': {'$sum': '$unique'}}},
            {'$project': {'_id': 0, 'sut': '$_id.sut', 'fuzzer': '$_id.fuzzer', 'exec': 1, 'crashes': 1, 'unique': 1}},
            {'$match': {'$or': [{'exec': {'$gt': 0}}, {'crashes': {'$gt': 0}}, {'unique': {'$gt': 0}}]}}
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
                                                                 exec=document['exec'],
                                                                 issues=document['crashes'],
                                                                 unique=document['unique'])
        return result

    def update_stat(self, sut, fuzzer, batch, issues):
        self._db.fuzzinator_stats.find_one_and_update({'sut': sut, 'fuzzer': fuzzer},
                                                      {'$inc': {'exec': int(batch), 'crashes': issues}},
                                                      upsert=True)
