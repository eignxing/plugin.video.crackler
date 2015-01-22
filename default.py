########################################################
## IMPORT
########################################################
import re
import urllib2, urllib
import urlparse
import json
import xbmcgui, xbmcplugin
from xbmcgui import ListItem
from datetime import datetime

########################################################
## VARS
########################################################

channel_detail_url = 'http://api.crackle.com/Service.svc/channel/%s/folders/us?format=json'
movies_json_url = 'http://api.crackle.com/Service.svc/browse/movies/full/all/alpha/us?format=json'
#originals_json_url = 'http://api.crackle.com/Service.svc/browse/originals/full/all/alpha/us?format=json'
tv_json_url = 'http://api.crackle.com/Service.svc/browse/shows/full/all/alpha/us?format=json'
base_media_url = 'http://media-%s-am.crackle.com/%s'
prog = re.compile(r''+'\/.\/.\/.{2}\/.{5}_')
object_cnt = 0
movies_map = ''
originals_map = ''
tv_map = ''

crackler_version = '1.0.1'

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
mode = args.get('mode', None)

########################################################
## FUNCTIONS
########################################################
def build_url(query):
    return base_url + '?' + urllib.urlencode(query)

def add_directory(title, image_url, url):
    li = xbmcgui.ListItem(title, iconImage=image_url)
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

def add_video_item(title, image_url, file_url, m_index, map_type, video_type):
    if map_type != '':
        li = xbmcgui.ListItem(title, iconImage=image_url)
        li.setProperty('mimetype', 'video')
        li.setProperty('IsPlayable', 'true')
        
        if video_type == 0: #Movie
            if len(str(map_type['Entries'][m_index]['ReleaseYear'])) == 4:
                li.setInfo('video', {'year': int(map_type['Entries'][m_index]['ReleaseYear'])})
            if len(str(map_type['Entries'][m_index]['DurationInSeconds'])) > 0:
                li.addStreamInfo('video', { 'duration': int(map_type['Entries'][m_index]['DurationInSeconds'])})
            else: print video_type, m_index, map_type['Entries'][m_index]['DurationInSeconds']
            li.setInfo('video', { 'genre': map_type['Entries'][m_index]['Genre'],'title': map_type['Entries'][m_index]['Title'], 
                'mpaa': map_type['Entries'][m_index]['Rating'], 'plot': map_type['Entries'][m_index]['Description']})
        elif video_type == 1: #TV
            #print m_index, map_type['FolderList'][0]['PlaylistList'][0]['MediaList'][m_index]['ReleaseDate']
            temp_ryear = map_type['FolderList'][0]['PlaylistList'][0]['MediaList'][m_index]['ReleaseDate']
            if temp_ryear.find('/') != -1:
                temp_ryear = int(temp_ryear[-4:])
                li.setInfo('video', {'year': temp_ryear})
            if len(str(map_type['FolderList'][0]['PlaylistList'][0]['MediaList'][m_index]['DurationInSeconds'])) > 0:
                li.addStreamInfo('video', { 'duration': int(map_type['FolderList'][0]['PlaylistList'][0]['MediaList'][m_index]['DurationInSeconds'])})
            else: print video_type, m_index, map_type['FolderList'][0]['PlaylistList'][0]['MediaList'][m_index]['DurationInSeconds']
            li.setInfo('video', { 'tvshowtitle': map_type['FolderList'][0]['PlaylistList'][0]['MediaList'][m_index]['ParentChannelName']})
            li.setInfo('video', { 'episode': int(map_type['FolderList'][0]['PlaylistList'][0]['MediaList'][m_index]['Episode'])})
            #if len(str(map_type['FolderList'][0]['PlaylistList'][0]['MediaList'][m_index]['ReleaseDate'])) > 0:
                #li.setInfo('video', { 'aired': str(datetime.strptime(map_type['FolderList'][0]['PlaylistList'][0]['MediaList'][m_index]['ReleaseDate'], '%m/%d/%Y').strftime('%Y-%m-%d'))})
            li.setInfo('video', { 'genre': map_type['FolderList'][0]['PlaylistList'][0]['MediaList'][m_index]['Genre'],'year': temp_ryear,'title': map_type['FolderList'][0]['PlaylistList'][0]['MediaList'][m_index]['Title'], 
                'mpaa': map_type['FolderList'][0]['PlaylistList'][0]['MediaList'][m_index]['Rating'], 'plot': map_type['FolderList'][0]['PlaylistList'][0]['MediaList'][m_index]['Description']})
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=file_url, listitem=li)
        #xbmcplugin.addSortMethod(int(m_index), xbmcplugin.SORT_METHOD_DATE)

def play_video():
    li = xbmcgui.ListItem(path=url)
    xbmcplugin.setResolvedUrl( handle=addon_handle, succeeded=True, listitem=li)

def retrieve_play_url(channel_id):
    play_url = ''
    jsonurl = urllib2.urlopen(channel_detail_url % (channel_id))
    channel_detail_map = json.loads(jsonurl.read())
    if channel_detail_map['status']['messageCodeDescription'] == 'OK':
        if int(channel_detail_map['Count']) > 0:
            i = 0
            while i < int(channel_detail_map['Count']):
                print channel_detail_map['FolderList'][i]['Name']
                if channel_detail_map['FolderList'][i]['Name'] == 'Movie':
                    pre_path = prog.findall(channel_detail_map['FolderList'][i]['PlaylistList'][0]['MediaList'][0]['Thumbnail_Wide'])
                    play_url = base_media_url % ('us', pre_path[0]) + '480p_1mbps.mp4'
                    #print channel_detail_map['FolderList'][i]['PlaylistList'][0]['MediaList'][0]['Title'] + " " + play_url
                elif channel_detail_map['FolderList'][i]['PlaylistList'][0]['MediaList'][0]['MediaType'] == 'Feature Film':
                    pre_path = prog.findall(channel_detail_map['FolderList'][i]['PlaylistList'][0]['MediaList'][0]['Thumbnail_Wide'])
                    play_url = base_media_url % ('us', pre_path[0]) + '480p_1mbps.mp4'

                i += 1
        else:
            print "crackler playback error: " + int(channel_detail_map['Count'])
    else:
        print "crackler playback error: " + channel_detail_map['status']['messageCodeDescription']
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
    # url_dat = build_url({'mode': 'originals_folder', 'foldername': 'Originals'})
    # add_directory('Originals', 'DefaultFolder.png', url_dat)

    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'movies_folder':
    xbmcplugin.setContent(addon_handle, 'movies')
    jsonurl = urllib2.urlopen(movies_json_url)
    movies_map = json.loads(jsonurl.read())

    if movies_map['status']['messageCodeDescription'] == 'OK':
        object_cnt = int(movies_map['Count'])
        if object_cnt > 0:
            i = 0
            while i < object_cnt:
                add_video_item((movies_map['Entries'][i]['Name']).encode('utf-8'), movies_map['Entries'][i]['OneSheetImage_800_1200'], sys.argv[0]+'?mode=play_video&v_id='+str(movies_map['Entries'][i]['ID']), i, movies_map, 0)
                i += 1
            print 'crackler: done listing movie items'
    
    xbmcplugin.endOfDirectory(addon_handle)

# elif mode[0] == 'originals_folder': #not yet implemented
    # jsonurl = urllib2.urlopen(originals_json_url)
    # originals_map = json.loads(jsonurl.read())
    # if originals_map['status']['messageCodeDescription'] == 'OK':
    #     object_cnt = int(originals_map['Count'])
    #     if object_cnt > 0:
    #         i = 0
    #         while i < object_cnt:
    #             add_video_item((originals_map['Entries'][i]['Name']).encode('utf-8'), originals_map['Entries'][i]['OneSheetImage_800_1200'], sys.argv[0]+'?mode=play_video&v_id='+str(originals_map['Entries'][i]['ID']), i, originals_map, 0)
    #             i += 1
    #         print 'crackler: done listing originals items'
    #xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'tv_folder':
    xbmcplugin.setContent(addon_handle, 'tvshows')
    jsonurl = urllib2.urlopen(tv_json_url)
    tv_map = json.loads(jsonurl.read())
    if tv_map['status']['messageCodeDescription'] == 'OK':
        object_cnt = int(tv_map['Count'])
        if object_cnt > 0:
            i = 0
            while i < object_cnt:
                add_directory((tv_map['Entries'][i]['Name']).encode('utf-8') , tv_map['Entries'][i]['OneSheetImage_800_1200'], sys.argv[0]+'?mode=view_episodes&indx='+str(i)+'&v_id='+str(tv_map['Entries'][i]['ID']))
                #add_video_item(tv_map['Entries'][i]['Name'], tv_map['Entries'][i]['OneSheetImage_800_1200'], sys.argv[0]+'?mode=play_video&v_id='+str(tv_map['Entries'][i]['ID']), i, tv_map)
                i += 1
            print 'crackler: done listing tv items'
    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'play_video':
    args_ar = urlparse.parse_qs(urlparse.urlparse(sys.argv[0]+sys.argv[2]).query)
    retrieve_play_url(args_ar['v_id'][0])
elif mode[0] == 'view_episodes':
    xbmcplugin.setContent(addon_handle, 'episodes')
    if len(tv_map) == 0:
        jsonurl = urllib2.urlopen(tv_json_url)
        tv_map = json.loads(jsonurl.read())

    args_ar = urlparse.parse_qs(urlparse.urlparse(sys.argv[0]+sys.argv[2]).query)
    jsonurl = urllib2.urlopen(channel_detail_url % (args_ar['v_id'][0]))
    channel_detail_map = json.loads(jsonurl.read())

    if channel_detail_map['status']['messageCodeDescription'] == 'OK':
        object_cnt = int(len(channel_detail_map['FolderList'][0]['PlaylistList'][0]['MediaList']))
        if object_cnt > 0:
            j = 0
            while j < object_cnt:
                pre_path = prog.findall(channel_detail_map['FolderList'][0]['PlaylistList'][0]['MediaList'][j]['Thumbnail_Wide'])
                play_url = base_media_url % ('us', pre_path[0]) + '480p_1mbps.mp4'
                add_video_item((channel_detail_map['FolderList'][0]['PlaylistList'][0]['MediaList'][j]['Title']).encode('utf-8') , tv_map['Entries'][int(args_ar['indx'][0])]['OneSheetImage_800_1200'], play_url, j, channel_detail_map, 1)
                j += 1
            print 'crackler: done listing tv items'
    xbmcplugin.endOfDirectory(addon_handle)

    args_ar = urlparse.parse_qs(urlparse.urlparse(sys.argv[0]+sys.argv[2]).query)

    xbmcplugin.endOfDirectory(addon_handle)