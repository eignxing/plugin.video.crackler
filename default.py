########################################################
## IMPORT
########################################################
import re
import urllib2, urllib
import urlparse
import json
import xbmcgui, xbmcplugin

########################################################
## VARS
########################################################

crackler_version = '1.0.6'

en_countries = [ 'AU', 'CA', 'US' ]
es_countries = [ 'AR', 'BO', 'CL', 'CO', 'CR', 'DO', 'EC', 'SV', 'GT', 'HN', 'MX', 'NI', 'PA', 'PY', 'PE', 'UY', 'VE' ]
pt_countries = [ 'BR' ]

supported_countries = {}
for r, a, m in (en_countries, 'api', 'us'), (es_countries, 'api-es', 'es'), (pt_countries, 'api-br', 'br'):
    for k in r:
        supported_countries[k] = a, m

country_json_url = 'http://api.crackle.com/Service.svc/geo/country?format=json'
channel_json_url = 'http://%s.crackle.com/Service.svc/channel/%s/folders/%s?format=json'
movies_json_url = 'http://%s.crackle.com/Service.svc/browse/movies/full/all/alpha/%s?format=json'
tv_json_url = 'http://%s.crackle.com/Service.svc/browse/shows/full/all/alpha/%s?format=json'
media_url = 'http://media-%s-am.crackle.com/%s480p_1mbps.mp4'
prog = re.compile('\/.\/.\/.{2}\/.{5}_')

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = dict([ (k, v[0]) for k, v in urlparse.parse_qs(sys.argv[2].replace('?', '')).items() ])
mode = args.get('mode', None)
country = args.get('country', None)
if country not in supported_countries:
    country = 'US'

########################################################
## FUNCTIONS
########################################################

def build_url(query):
    return '%s?%s' % (base_url, urllib.urlencode(query))

def add_common_sort_methods():
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_DURATION)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_MPAA_RATING)

def add_directory(title, image_url, url):
    li = xbmcgui.ListItem(title, iconImage=image_url)
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

def add_movie_item(info, file_url):
    li = xbmcgui.ListItem(info['Name'].encode('utf-8'), iconImage=info['OneSheetImage_800_1200'])
    li.setProperty('mimetype', 'video/mp4')
    li.setProperty('IsPlayable', 'true')
    duration = info['DurationInSeconds']
    if duration is not None:
        li.addStreamInfo('video', { 'duration': int(duration) })
    d = { 'title': info['Title'], 'year': info['ReleaseYear'], 'genre': info['Genre'], 'mpaa': info['Rating'], 'plot': info['Description'] }
    for k, v in d.items():
        li.setInfo('video', { k: v })
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=file_url, listitem=li)

def add_tv_item(info, file_url):
    li = xbmcgui.ListItem(info['Title'].encode('utf-8'), iconImage=info['OneSheetImage800x1200'])
    li.setProperty('mimetype', 'video/mp4')
    li.setProperty('IsPlayable', 'true')
    li.addStreamInfo('video', { 'duration': int(info['DurationInSeconds']) })
    d = { 'title': info['Title'], 'genre': info['Genre'], 'mpaa': info['Rating'], 'plot': info['Description'], 'tvshowtitle': info['ParentChannelName'] }
    temp_season = info['Season']
    temp_episode = info['Episode']
    if len(temp_episode) > 0:
        d['episode'] = int(temp_episode)
    if len(temp_season) > 0:
        d['season'] = int(temp_season)
    if len(temp_episode) > 0 and len(temp_season) > 0:
        d['title'] = u'%s (S%sE%s)' % (d['title'], temp_season, temp_episode) 
    date = info['ReleaseDate'].split('/')
    if len(date) == 3:
        temp_rmonth = int(date[0])
        temp_rday = int(date[1])
        temp_ryear = int(date[2])
        d['year'] = temp_ryear
        d['aired'] = u'%d-%02d-%02d' % (temp_ryear, temp_rmonth, temp_rday)

    for k, v in d.items():
        li.setInfo('video', { k: v })
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=file_url, listitem=li)

########################################################
## BODY
########################################################

if mode is None:
    # show your country
    jsonurl = urllib2.urlopen(country_json_url)
    country_data = json.loads(jsonurl.read())
    r = country_data.get('CountryCode', None)
    if r in supported_countries:
        country = r
    # show a choice of movies or tv
    add_directory('Movies', 'DefaultFolder.png', build_url({'mode': 'movies_folder', 'foldername': 'Movies', 'country': country}))
    add_directory('TV', 'DefaultFolder.png', build_url({'mode': 'tv_folder', 'foldername': 'TV', 'country': country}))
    xbmcplugin.endOfDirectory(addon_handle)
elif mode == 'movies_folder':
    # show a list of movies
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE, '%Y')
    add_common_sort_methods()
    xbmcplugin.setContent(addon_handle, 'movies')
    jsonurl = urllib2.urlopen(movies_json_url % (supported_countries[country][0], country))
    movies_map = json.loads(jsonurl.read())
    if movies_map['status']['messageCodeDescription'] == 'OK':
        for info in movies_map['Entries']:
            add_movie_item(info, build_url({'mode': 'play_video', 'v_id': str(info['ID']), 'country': country}))
    xbmcplugin.endOfDirectory(addon_handle)
elif mode == 'play_video':
    # play the selected video
    play_url = ''
    jsonurl = urllib2.urlopen(channel_json_url % (supported_countries[country][0], args['v_id'], country))
    channel_detail_map = json.loads(jsonurl.read())
    if channel_detail_map['status']['messageCodeDescription'] == 'OK':
        for folder in channel_detail_map['FolderList']:
            for playlist in folder['PlaylistList']:
                for info in playlist['MediaList']:
                    if info['MediaType'] == 'Feature Film':
                        play_url = media_url % (supported_countries[country][1], prog.findall(info['Thumbnail_Wide'])[0])
                        break
    li = xbmcgui.ListItem(path=play_url)
    xbmcplugin.setResolvedUrl(handle=addon_handle, succeeded=True, listitem=li)
elif mode == 'tv_folder':
    # show a list of tv shows
    jsonurl = urllib2.urlopen(tv_json_url % (supported_countries[country][0], country))
    tv_map = json.loads(jsonurl.read())
    if tv_map['status']['messageCodeDescription'] == 'OK':
        for info in tv_map['Entries']:
            add_directory(info['Name'].encode('utf-8'), info['OneSheetImage_800_1200'], build_url({'mode': 'view_episodes', 'v_id': str(info['ID']), 'country': country}))
    xbmcplugin.endOfDirectory(addon_handle)
elif mode == 'view_episodes':
    # show a list of episodes for the selected tv show
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_EPISODE)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE, '%D')
    add_common_sort_methods()
    xbmcplugin.setContent(addon_handle, 'episodes')
    jsonurl = urllib2.urlopen(channel_json_url % (supported_countries[country][0], args['v_id'], country))
    channel_detail_map = json.loads(jsonurl.read())
    if channel_detail_map['status']['messageCodeDescription'] == 'OK':
        for folder in channel_detail_map['FolderList']:
            for playlist in folder['PlaylistList']:
                for info in playlist['MediaList']:
                    add_tv_item(info, media_url % (supported_countries[country][1], prog.findall(info['Thumbnail_Wide'])[0]))
    xbmcplugin.endOfDirectory(addon_handle)
