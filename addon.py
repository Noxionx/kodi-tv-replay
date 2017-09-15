# -*- coding: utf-8 -*-
# Module: default
# Author: Roman V. M.
# Created on: 28.11.2014
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import sys
import urllib2
from urllib import urlencode
from urlparse import parse_qsl
import xbmcgui
import xbmcplugin
import re
import json
try:
    # Python 2.6-2.7
    from HTMLParser import HTMLParser
except ImportError:
    # Python 3
    from html.parser import HTMLParser

# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])

CATEGORIES = {
    'series-et-fictions': ['feuilletons', 'telefilms', 'series-policieres-thrillers', 'series-fantastiques', 'series-comedies', 'series-dramatiques', 'courts-metrages'],
    'documentaires': ['histoire', 'animaux-nature', 'societe', 'art-culture', 'environnement', 'science-sante', 'politique', 'sport', 'voyages'],
    'actualites-et-societe': ['info-meteo', 'reportages', 'magazines-d-actu', 'temoignages', 'emissions-culturelles', 'sante', 'politique', 'religion'],
    'spectacles-et-culture': ['emissions-culturelles', 'theatre-danse-opera', 'musique-concerts', 'litterature'],
    'vie-quotidienne': ['deco-maison', 'cuisine', 'mode', 'bien-etre', 'vie-pratique'],
    'jeux-et-divertissements': ['jeux', 'divertissements', 'emissions-musicales']
}


def get_url(**kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.

    :param kwargs: "argument=value" pairs
    :type kwargs: dict
    :return: plugin call URL
    :rtype: str
    """
    return '{0}?{1}'.format(_url, urlencode(kwargs))


def get_categories():
    """
    Get the list of video categories.

    Here you can insert some parsing code that retrieves
    the list of video categories (e.g. 'Movies', 'TV-shows', 'Documentaries' etc.)
    from some site or server.

    .. note:: Consider using `generator functions <https://wiki.python.org/moin/Generators>`_
        instead of returning lists.

    :return: The list of video categories
    :rtype: list
    """
    return CATEGORIES.iterkeys()

def get_subcategories(category):
    return CATEGORIES[category]

def get_videos_from_page(url):
    h = HTMLParser()
    videos = []
    page = h.unescape(urllib2.urlopen(url).read().decode('utf8').replace('\n',''))
    m = re.findall('<li.*?>.*?</li>', page)
    if m == None:
        return

    for match in m:
        mbuy = re.search('€', match)
        mid = re.search('<a.*?data-video=\"(.+?)\".*?>', match)
        mtitle = re.search('<a.*?title=\"(.+?)\".*?>', match)
        msubtitle = re.search('<p class=\"fs_sm brown_l mb_5 c_black mb_5\">\s*(.+?)\s*</p>', match)
        mimg = re.search('<img.*?data-src=\"(.+?)\".*?>', match)
        mdate = re.search('<p class=\"pa b_30 fs_sm brown_l c_brownish-grey\">.*?([\d.]*?).*?</p>', match)
        if mbuy == None and not (mid == None):
            title = ''
            subtitle = ''
            img = ''
            date = ''
            if not (mtitle == None):
                title = mtitle.group(1)
            if not (msubtitle == None):
                subtitle = msubtitle.group(1)
                if not(subtitle == title):
                    title = '%s - %s' % (title, subtitle)
            if not (mimg == None):
                img = 'https:%s' % (mimg.group(1))
            if not (mdate == None):
                date = mdate.group(1)
            videos.append(dict({
                'id': mid.group(1),
                'title': title,
                'img': img,
                'date': date
            }))
    return videos

def fetch_videos(category, subcategory):
    allvideos = []
    i = 0
    while True:
        url = 'https://www.france.tv/%s_%s/contents?page=%s' % (category, subcategory, str(i))
        print(url)
        videos = get_videos_from_page(url)
        print(len(videos))
        if len(videos) == 0 or i >= 20:
            break
        allvideos.extend(videos)
        i += 1
    return allvideos


def get_video_url(id):
    url = 'https://sivideo.webservices.francetelevisions.fr/tools/getInfosOeuvre/v2/?idDiffusion=%s' % (id)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.79 Safari/537.36'
    }
    r = urllib2.Request(url, headers=headers)

    h = HTMLParser()
    page = h.unescape(urllib2.urlopen(r).read().decode('utf8'))
    video_info = json.loads(page)
    for video_format in video_info['videos']:
        if video_format['format'] == 'm3u8-download':
            return video_format['url_secure']


def list_categories():
    """
    Create the list of video categories in the Kodi interface.
    """
    # Get video categories
    categories = get_categories()
    # Iterate through categories
    for category in categories:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=category)
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        #list_item.setArt({'thumb': VIDEOS[category][0]['thumb'],
        #                  'icon': VIDEOS[category][0]['thumb'],
        #                  'fanart': VIDEOS[category][0]['thumb']})
        # Set additional info for the list item.
        # Here we use a category name for both properties for for simplicity's sake.
        # setInfo allows to set various information for an item.
        # For available properties see the following link:
        # http://mirrors.xbmc.org/docs/python-docs/15.x-isengard/xbmcgui.html#ListItem-setInfo
        list_item.setInfo('video', {'title': category, 'genre': category})
        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=listing&category=Animals
        url = get_url(action='listing', category=category)
        # is_folder = True means that this item opens a sub-list of lower level items.
        is_folder = True
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def list_subcategories(category):
    """
    Create the list of video subcategories in the Kodi interface.
    """
    # Get video categories
    subcategories = get_subcategories(category)
    # Iterate through categories
    for subcategory in subcategories:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=subcategory)
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        #list_item.setArt({'thumb': VIDEOS[category][0]['thumb'],
        #                  'icon': VIDEOS[category][0]['thumb'],
        #                  'fanart': VIDEOS[category][0]['thumb']})
        # Set additional info for the list item.
        # Here we use a category name for both properties for for simplicity's sake.
        # setInfo allows to set various information for an item.
        # For available properties see the following link:
        # http://mirrors.xbmc.org/docs/python-docs/15.x-isengard/xbmcgui.html#ListItem-setInfo
        list_item.setInfo('video', {'title': subcategory, 'genre': subcategory})
        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=listing&category=Animals
        url = get_url(action='listing', category=category, subcategory=subcategory)
        # is_folder = True means that this item opens a sub-list of lower level items.
        is_folder = True
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)


def list_videos(category, subcategory):
    """
    Create the list of playable videos in the Kodi interface.

    :param category: Category name
    :type category: str
    """
    # Get the list of videos in the category.
    videos = fetch_videos(category, subcategory)
    # Iterate through videos.
    for video in videos:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=video['title'])
        # Set additional info for the list item.
        list_item.setInfo('video', {'title': video['title'], 'date': video['date']})
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        list_item.setArt({'thumb': video['img'], 'icon': video['img'], 'fanart': video['img']})
        # Set 'IsPlayable' property to 'true'.
        # This is mandatory for playable items!
        list_item.setProperty('IsPlayable', 'true')
        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=play&video=http://www.vidsplay.com/wp-content/uploads/2017/04/crab.mp4
        url = get_url(action='play', video=video['id'])
        # Add the list item to a virtual Kodi folder.
        # is_folder = False means that this item won't open any sub-list.
        is_folder = False
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_DATEADDED)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)


def play_video(id):
    """
    Play a video by the provided path.

    :param id: videoId
    :type id: str
    """
    url = get_video_url(id)
    # Create a playable item with a path to play.
    play_item = xbmcgui.ListItem(path=url)
    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)


def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring

    :param paramstring: URL encoded plugin paramstring
    :type paramstring: str
    """
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(parse_qsl(paramstring))
    # Check the parameters passed to the plugin
    if params:
        if params['action'] == 'listing' and 'category' in params:
            if not ('subcategory' in params):
                list_subcategories(params['category'])
            else:
                # Display the list of videos in a provided category and subcategory.
                list_videos(params['category'], params['subcategory'])
        elif params['action'] == 'play':
            # Play a video from a provided URL.
            play_video(params['video'])
        else:
            # If the provided paramstring does not contain a supported action
            # we raise an exception. This helps to catch coding errors,
            # e.g. typos in action names.
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        # If the plugin is called from Kodi UI without any parameters,
        # display the list of video categories
        list_categories()


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])
