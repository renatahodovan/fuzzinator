# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.md or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from pymongo import ASCENDING, MongoClient


class MongoDriver(object):

    def __init__(self, uri):
        self.uri = uri

    @property
    def _db(self):
        return MongoClient(self.uri).get_default_database()

    def init_db(self, sut_fuzzer_pairs):
        """
        Creates an 'fuzzinator_issues' collection with appropriate indexes (if
        not existing already), and initializes a 'fuzzinator_stats' collection
        for (sut, fuzzer) pairs (with 0 exec and crash counts if not existing
        already).
        """
        db = self._db

        issues = db.fuzzinator_issues
        issues.create_index([('sut', ASCENDING), ('id', ASCENDING)])

        stats = db.fuzzinator_stats
        for sut, fuzzer in sut_fuzzer_pairs:
            if stats.find({'sut': sut, 'fuzzer': fuzzer}).count() == 0:
                stats.insert_one({'sut': sut, 'fuzzer': fuzzer, 'exec': 0, 'crashes': 0})

    def add_issue(self, issue):
        result = self._db.fuzzinator_issues.update_one(
            {'id': issue['id'], 'sut': issue['sut']},
            {'$set': issue},
            upsert=True
        )
        issue['_id'] = result.upserted_id
        return result.matched_count == 0

    def all_issues(self):
        return list(self._db.fuzzinator_issues.find({}))

    def find_issue_by_id(self, id):
        return self._db.fuzzinator_issues.find_one({'_id': id})

    def update_issue(self, issue, _set):
        self._db.fuzzinator_issues.update_one({'id': issue['id'], 'sut': issue['sut']}, {'$set': _set})

    def remove_issue_by_id(self, _id):
        self._db.fuzzinator_issues.delete_one({'_id': _id})

    def stat_snapshot(self, fuzzers):
        db = self._db

        stat = dict()
        match = {'$or': [{'fuzzer': fuzzer} for fuzzer in fuzzers]} if fuzzers else {}

        if db.fuzzinator_issues.count() > 0:
            issues_stat = db.fuzzinator_issues.aggregate([
                {'$match': match},
                {'$group': {'_id': {'fuzzer': '$fuzzer'},
                            'unique': {'$sum': 1}}},
                {'$project': {'fuzzer': 1, 'unique': 1}}
            ])

            for document in issues_stat:
                fuzzer = document['_id']['fuzzer']
                stat[fuzzer] = dict(fuzzer=fuzzer,
                                    unique=document['unique'],
                                    crashes=0,
                                    exec=0)

        fuzzers_stat = db.fuzzinator_stats.aggregate([
            {'$match': match},
            {'$group': {'_id': {'fuzzer': '$fuzzer'},
                        'exec': {'$sum': '$exec'},
                        'crashes': {'$sum': '$crashes'}}},
            {'$project': {'fuzzer': 1, 'exec': 1, 'crashes': 1}}
        ])
        for document in fuzzers_stat:
            fuzzer = document['_id']['fuzzer']
            data = dict(fuzzer=fuzzer,
                        exec=document['exec'],
                        crashes=document['crashes'])

            if fuzzer in stat:
                stat[fuzzer].update(data)
            else:
                stat[fuzzer] = dict(unique=0, **data)
        return stat

    def update_stat(self, sut, fuzzer, batch, crashes):
        self._db.fuzzinator_stats.find_one_and_update({'sut': sut, 'fuzzer': fuzzer},
                                                      {'$inc': {'exec': int(batch), 'crashes': crashes}},
                                                      upsert=True)
