########################################################
## IMPORT
########################################################
import re, time
import urllib2, urllib
import urlparse
import json
import xbmcgui, xbmcplugin
from xbmcgui import ListItem
import datetime

########################################################
## VARS
########################################################

channel_detail_url = 'http://api.crackle.com/Service.svc/channel/%s/folders/us?format=json'
movies_json_url = 'http://api.crackle.com/Service.svc/browse/movies/full/all/alpha/us?format=json'
tv_json_url = 'http://api.crackle.com/Service.svc/browse/shows/full/all/alpha/us?format=json'
base_media_url = 'http://media-%s-am.crackle.com/%s'
prog = re.compile(r''+'\/.\/.\/.{2}\/.{5}_')

crackler_version = '1.0.6'

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
mode = args.get('mode', None)

########################################################
## FUNCTIONS
########################################################

def build_url(query):
    return base_url + '?' + urllib.urlencode(query)

def add_sort_methods(video_typ):
    if video_typ == 1: #TV
        xbmcplugin.addSortMethod(int(sys.argv[1]), 22)
        xbmcplugin.addSortMethod(int(sys.argv[1]), 10, '%D')
    elif video_typ == 0: #Movies
        xbmcplugin.addSortMethod(int(sys.argv[1]), 10, '%Y') #title, label2=year
    xbmcplugin.addSortMethod(int(sys.argv[1]), 17) #Year
    xbmcplugin.addSortMethod(int(sys.argv[1]), 8) #Duration
    xbmcplugin.addSortMethod(int(sys.argv[1]), 28) #MPAA

def add_directory(title, image_url, url):
    li = xbmcgui.ListItem(title, iconImage=image_url)
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

def add_video_item(title, image_url, file_url, m_index, map_typ, video_typ):
    if map_typ != '':
        li = xbmcgui.ListItem(title, iconImage=image_url)
        li.setProperty('mimetype', 'video/mp4')
        li.setProperty('IsPlayable', 'true')
        temp_ryear = ''
        temp_duration = ''
        temp_title = ''
        temp_genre = ''
        temp_mpaa = ''
        temp_plot = ''
        temp_tvshowtitle = ''
        temp_episode = ''
        temp_season = ''
        if video_typ == 0: #Movie
            temp_ryear = str(map_typ['Entries'][m_index]['ReleaseYear'])
            temp_duration = str(map_typ['Entries'][m_index]['DurationInSeconds'])
            temp_title = map_typ['Entries'][m_index]['Title']
            temp_genre = str(map_typ['Entries'][m_index]['Genre'])
            temp_mpaa = str(map_typ['Entries'][m_index]['Rating'])
            temp_plot = map_typ['Entries'][m_index]['Description']
        elif video_typ == 1: #TV
            temp_ryear = str(map_typ['FolderList'][0]['PlaylistList'][0]['MediaList'][m_index]['ReleaseDate'])
            temp_duration = str(map_typ['FolderList'][0]['PlaylistList'][0]['MediaList'][m_index]['DurationInSeconds'])
            temp_episode = str(map_typ['FolderList'][0]['PlaylistList'][0]['MediaList'][m_index]['Episode'])
            temp_season = str(map_typ['FolderList'][0]['PlaylistList'][0]['MediaList'][m_index]['Season'])
            if len(temp_episode) > 0 and len(temp_season) > 0:
                temp_title = map_typ['FolderList'][0]['PlaylistList'][0]['MediaList'][m_index]['Title'] + ' (S' + temp_season + 'E' + temp_episode + ')' 
            else:
                temp_title = map_typ['FolderList'][0]['PlaylistList'][0]['MediaList'][m_index]['Title']
            temp_genre = str(map_typ['FolderList'][0]['PlaylistList'][0]['MediaList'][m_index]['Genre'])
            temp_mpaa = str(map_typ['FolderList'][0]['PlaylistList'][0]['MediaList'][m_index]['Rating'])
            temp_plot = map_typ['FolderList'][0]['PlaylistList'][0]['MediaList'][m_index]['Description']
            temp_tvshowtitle = str(map_typ['FolderList'][0]['PlaylistList'][0]['MediaList'][m_index]['ParentChannelName'])

        if len(temp_ryear) == 4:
            li.setInfo('video', {'year': int(temp_ryear)})
        elif temp_ryear.find('/') != -1:
            li.setInfo('video', {'year': int(temp_ryear[-4:])})
            date_spl = temp_ryear.split("/")
            li.setInfo('video', {'aired': str(datetime.date(int(date_spl[2]), int(date_spl[0]), int(date_spl[1])).strftime('%Y-%m-%d'))})
        if len(temp_duration) > 0 and temp_duration != "None":
            li.addStreamInfo('video', { 'duration': int(temp_duration)})
        if len(temp_title) > 0:
            li.setInfo('video', {'title': temp_title})
        if len(temp_genre) > 0:
            li.setInfo('video', {'genre': temp_genre})
        if len(temp_mpaa) > 0:
            li.setInfo('video', {'mpaa': temp_mpaa})
        if len(temp_plot) > 0:
            li.setInfo('video', {'plot': temp_plot}) 
        if len(temp_tvshowtitle) > 0:
            li.setInfo('video', {'tvshowtitle': temp_tvshowtitle})
        if len(temp_episode) > 0:
            li.setInfo('video', {'episode': int(temp_episode)})
        if len(temp_season) > 0:
            li.setInfo('video', {'season': int(temp_season)})

        xbmcplugin.addDirectoryItem(handle=addon_handle, url=file_url, listitem=li)

def play_video():
    li = xbmcgui.ListItem(path=url)
    xbmcplugin.setResolvedUrl( handle=addon_handle, succeeded=True, listitem=li)

def retrieve_play_url(channel_id):
    play_url = ''
    jsonurl = urllib2.urlopen(channel_detail_url % (channel_id))
    channel_detail_map = json.loads(jsonurl.read())
    if channel_detail_map['status']['messageCodeDescription'] == 'OK':
        for info in channel_detail_map['FolderList']:
            if info['Name'] == 'Movie':
                pre_path = prog.findall(info['PlaylistList'][0]['MediaList'][0]['Thumbnail_Wide'])
                play_url = base_media_url % ('us', pre_path[0]) + '480p_1mbps.mp4'
            elif info['PlaylistList'][0]['MediaList'][0]['MediaType'] == 'Feature Film':
                pre_path = prog.findall(info['PlaylistList'][0]['MediaList'][0]['Thumbnail_Wide'])
                play_url = base_media_url % ('us', pre_path[0]) + '480p_1mbps.mp4'
        else:
            xbmc.log("crackler playback error: " + str(channel_detail_map['Count']), level=xbmc.LOGDEBUG)
    else:
        xbmc.log("crackler playback error: " + str(channel_detail_map['status']['messageCodeDescription']), level=xbmc.LOGDEBUG)

    li = xbmcgui.ListItem(path=play_url)
    xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=li)

########################################################
## BODY
########################################################


if mode is None:
    url_dat = build_url({'mode': 'movies_folder', 'foldername': 'Movies'})
    add_directory('Movies', 'DefaultFolder.png', url_dat)
    url_dat = build_url({'mode': 'tv_folder', 'foldername': 'TV'})
    add_directory('TV', 'DefaultFolder.png', url_dat)

    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'movies_folder':
    add_sort_methods(0)
    xbmcplugin.setContent(addon_handle, 'movies')

    jsonurl = urllib2.urlopen(movies_json_url)
    movies_map = json.loads(jsonurl.read())
    if movies_map['status']['messageCodeDescription'] == 'OK':
        for i, info in enumerate(movies_map['Entries']):
            if info['DurationInSeconds'] is not None and info['UserRating'] is not None:
                add_video_item(info['Name'].encode('utf-8'), info['OneSheetImage_800_1200'], sys.argv[0]+'?mode=play_video&v_id='+str(info['ID']), i, movies_map, 0)

    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'tv_folder':
    jsonurl = urllib2.urlopen(tv_json_url)
    tv_map = json.loads(jsonurl.read())
    if tv_map['status']['messageCodeDescription'] == 'OK':
        for info in tv_map['Entries']:
            add_directory(info['Name'].encode('utf-8') , info['OneSheetImage_800_1200'], sys.argv[0]+'?mode=view_episodes&v_id='+str(info['ID']))
    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'play_video':
    args_ar = dict(urlparse.parse_qsl(sys.argv[2].replace('?','')))
    retrieve_play_url(args_ar['v_id'])
elif mode[0] == 'view_episodes':
    add_sort_methods(1)
    xbmcplugin.setContent(addon_handle, 'episodes')

    args_ar = dict(urlparse.parse_qsl(sys.argv[2].replace('?','')))
    jsonurl = urllib2.urlopen(channel_detail_url % (args_ar['v_id']))
    channel_detail_map = json.loads(jsonurl.read())

    if channel_detail_map['status']['messageCodeDescription'] == 'OK':
        for i, info in enumerate(channel_detail_map['FolderList'][0]['PlaylistList'][0]['MediaList']):
            pre_path = prog.findall(info['Thumbnail_Wide'])
            play_url = base_media_url % ('us', pre_path[0]) + '480p_1mbps.mp4'
            add_video_item(info['Title'].encode('utf-8') , info['OneSheetImage800x1200'], play_url, i, channel_detail_map, 1)
    xbmcplugin.endOfDirectory(addon_handle)
