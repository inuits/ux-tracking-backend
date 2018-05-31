from flask_restful import reqparse

optsParser = reqparse.RequestParser()
optsParser.add_argument('reverse', type=bool, location='args')


class EsOptions(object):

    def __init__(self):
        self.esOpts = {}
        self.matches = {}
        self.filters = {
            'include': {},
            'exclude': {}
        }
        self.setPaging()

        reverse = optsParser.parse_args()['reverse']
        self.setDefaultSorting(reverse)

    def setPaging(self):
        paging = reqparse.RequestParser()
        paging.add_argument('limit', type=int, location='args')
        paging.add_argument('from', type=int, location='args')

        args = paging.parse_args()
        self.esOpts['size'] = args['limit'] if not args['limit'] is None else 100
        self.esOpts['from'] = args['from'] if not args['from'] is None else 0

    def setSorting(self, sortingmethod):
        self.esOpts['sort'] = sortingmethod

    def setDefaultSorting(self, reverse=False):
        if not reverse:
            self.setSorting({
                'timestamp': {'order': 'desc'}
            })
        else:
            self.setSorting({
                'timestamp': {'order': 'asc'}
            })

    def addQuery(self, key, value):
        if not value is None:
            self.matches[key] = value

    def addFilter(self, key: str, value: str):
        if not value is None:
            if ',' in value:
                for val in value.split(','):
                    self.addFilter(key, val)
            else:
                incType = 'exclude' if value.startswith('!') else 'include'
                if not key in self.filters[incType]:
                    self.filters[incType][key] = []

                self.filters[incType][key].append(value[1:] if value.startswith('!') else value)

    def get(self):
        if self.matches:
            self.__addKeyIfNotExists__(self.esOpts, 'query')
            self.esOpts['query']['match'] = self.matches

        if self.filters:
            self.__addKeyIfNotExists__(self.esOpts, 'query')
            self.esOpts['query']['bool'] = {'must': [], 'must_not': []}
            self.esOpts['query']['bool']['must'].append({'bool': {'should': []}})

            for key, value in self.filters['include'].items():
                if len(value) == 1:
                    self.esOpts['query']['bool']['must'].append({'term': {key: value[0]}})
                else:
                    for item in value:
                        self.esOpts['query']['bool']['must'][0]['bool']['should'].append({'term': {key: item}})

            for key, value in self.filters['exclude'].items():
                if len(value) == 1:
                    self.esOpts['query']['bool']['must_not'].append({'term': {key: value[0]}})
                else:
                    for item in value:
                        self.esOpts['query']['bool']['must_not'].append({'term': {key: item}})

        return self.esOpts

    def __addKeyIfNotExists__(self, dict: dict, key):
        if not key in dict:
            dict[key] = {}