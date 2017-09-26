from enum import Enum
import aiohttp
import asyncio
import async_timeout
import urllib.parse


async def fetch_json(session, url, params):
    """Fetch json response from given url"""
    async with session.get(url, params=params) as response:
        return await response.json()

async def feth_json_with_standard_timeout(session, url, params):
    """Fetch json response from given url within the standard timeout"""
    with async_timeout.timeout(30):
        return await fetch_json(session, url, params)

async def call8tracks(session, path, params, return_format, version):
    """Get json reponse from 8tracks api for given parameters and path"""
    url = "http://8tracks.com" + path
    common_params = {'api_version':version, 'format':return_format}
    params.update(common_params)
    return await feth_json_with_standard_timeout(session, url, params)





class query_8tracks:
    def __init__(self):
        self.path = ''
        self.params = dict()

    async def get_results(self):
        """fire the query!"""
        async with aiohttp.ClientSession() as session:
            return await call8tracks(session, self.path, self.params, 'jsonh', '3')

class SortTypes(Enum):
    hot = 1
    recent = 2
    popular = 3


class query_8tracks_mixdetails(query_8tracks):
    def __init__(self):
        """constructor"""
        query_8tracks.__init__(self)
    
    def of_id(self, mix_id: int):
        self.path = '/mixes/' + str(mix_id) + '/tracks_for_international'
        return self

    async def get_results_cleaned(self):
        """fire the query!"""
        results_json = await self.get_results()
        #print("results : ")
        #print(results_json)
        result = dict()
        for track in results_json['tracks']:
            result[track['id']] = track['performer'] + ' ' + track['name']
        return result

class query_8tracks_mixsets(query_8tracks):
    """This class represents a query for 8 tracks mix sets"""
    def __init__(self):
        """constructor"""
        query_8tracks.__init__(self)

    def init(self):
        """Initialize the query object"""
        self.path = "/mix_sets"
        self.params = {'include':'mixes'}

    def all(self):
        """Get all mix sets"""
        self.init()
        self.path = self.path + "/all"
        return self

    def sort(self, sort_type: SortTypes):
        """Sort result by type"""
        if sort_type == SortTypes.hot:
            self.path = self.path + ":hot"
        elif sort_type == SortTypes.popular:
            self.path = self.path + ":popular"
        elif sort_type == SortTypes.recent:
            self.path = self.path + ":recent"
        return self

    @staticmethod
    def clean_slug(slug):
        """Clean 8tracks slug parameters"""
        cleaned_slug = slug.replace('_', '__').replace(' ', '_').replace('/', '\\').replace('.', '^')
        cleaned_slug = urllib.parse.quote(cleaned_slug.encode("utf-8"))
        return cleaned_slug

    @staticmethod
    def clean_slugs(slugs: list):
        """Clean 8tracks slug parameters"""
        joined_slugs = '+'.join(slugs)
        cleaned_slugs = query_8tracks_mixsets.clean_slug(joined_slugs)
        return cleaned_slugs

    def by_tags(self, tags: list):
        """Get mix sets for these tag"""
        self.init()
        self.path = self.path + "/tags"
        self.path = self.path + ":" + query_8tracks_mixsets.clean_slugs(tags)
        return self

    def by_artist(self, artist_name):
        """Get mix sets for this artist"""
        self.init()
        self.path = self.path + "/artist"
        self.path = self.path + ":" + query_8tracks_mixsets.clean_slug(artist_name)
        return self

    def by_keyword(self, keyword):
        self.init()
        self.path = self.path + "/keyword"
        self.path = self.path + ":" + query_8tracks_mixsets.clean_slug(keyword)
        return self
    
    def top(self, count):
        """get top n records"""
        self.params['include'] = 'mixes+pagination'
        self.params['page'] = str(1)
        self.params['per_page'] = str(count)
        return self

    def page(self, count_per_page: int, page_number: int):
        """paginate the results from 8track"""
        self.params['include'] = 'mixes+pagination'
        self.params['page'] = str(page_number)
        self.params['per_page'] = str(count_per_page)
        return self
    
    async def get_results_cleaned(self):
        """fire the query!"""
        results_json = await self.get_results()
        result = dict()
        for mix in results_json['mix_set']['mixes']:
            result[mix['id']] = mix['name']
        return result


