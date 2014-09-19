__author__ = 'Robin Altena'
from django.db import models
from django.db.models import query, Q
import operator

class ActivityManager(models.Manager):

	def get_query_set(self):
		return ActivityQuerySet(self.model, using=self._db)

	def search(self, query, search_fields):
		return self.get_query_set().search(query, search_fields)

	def filter_years(self, years):
		return self.get_query_set().filter_years(years)

class ActivityQuerySet(query.QuerySet):
	class Meta:
		DEFAULT_SEARCH_FIELDS = ('titles', 'descriptions', 'identifiers')
		#@TODO search in identifier or id??
		SEARCHABLE_PROPERTIES = {
			#@TODO Change search methods to FTS where possible
			'identifiers':	{'name': 'activitysearchdata__search_identifier', 'method':''},
			'titles':		{'name': 'activitysearchdata__search_title', 'method': '__search'},
			'descriptions':	{'name': 'activitysearchdata__search_description', 'method': '__search'},
			'countries':	{'name': 'activitysearchdata__search_country_name', 'method': '__search'},
			'regions':		{'name': 'activitysearchdata__search_region_name', 'method': '__search'},
			'sectors':		{'name': 'activitysearchdata__search_sector_name', 'method': '__search'},
			'part_organisations':{'name': 'activitysearchdata__search_participating_organisation_name', 'method': '__search'},
			'rep_organisations':{'name': 'activitysearchdata__search_reporting_organisation_name', 'method': '__search'},
			'documents':	{'name': 'activitysearchdata__search_documentlink_title', 'method': '__search'},

		}

	#@TODO This should be implemented  as Queryset.as_manager() after we move to django 1.7
	def search(self, query, search_fields):
		prepared_filter = self._prepare_search_filter(self.Meta.DEFAULT_SEARCH_FIELDS if search_fields == None else search_fields, query)
		return self.filter(reduce(operator.or_, [Q(f) for f in prepared_filter]))

	def distinct_if_necessary(self, applicable_filters):
		for key in applicable_filters:
			if key[-4:] == '__in':
				return self.distinct()
		return self

	def filter_years(self, years):
		prepared_filter = []

		try:
			for f in years:
				prepared_filter.append(Q(**{'start_planned__year':f}))
		except TypeError:
			prepared_filter.append(Q(**{'start_planned__year':years}))

		if len(prepared_filter) > 1:
			return self.filter(reduce(operator.or_, prepared_filter))
		else: return self.filter(prepared_filter[0])

	def _create_full_text_query(self, query):
		'''Modifies the query for full text search boolean mode. This adds a + and * char to each word. + sets boolean AND search. * activates wildcard search'''
		fts_query = ''
		for word in query.split():
			fts_query += '+' + word+'* '
		fts_query = fts_query[:-1]
		return fts_query

	def _prepare_search_filter(self, search_fields, query):
		fts_query = self._create_full_text_query(query)
		prepared_filter = []
		for field in  search_fields:
			if field in self.Meta.SEARCHABLE_PROPERTIES:
				property = self.Meta.SEARCHABLE_PROPERTIES.get(field)
				prepared_filter.append((property.get('name')+property.get('method'), fts_query if property.get('method') == '__search' else query))
			else: raise Exception('unsupported search_field. Choices are: ' +  str(self.Meta.SEARCHABLE_PROPERTIES.keys()))
		return prepared_filter
