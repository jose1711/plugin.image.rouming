# -*- coding: utf-8 -*-
# plugin for viewing pics on rouming.cz on kodi. browsing archive
# is currently not supported

import re
import sys
import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin
import util
from HTMLParser import HTMLParser

g_AddonHandle = int(sys.argv[1])
g_AddonPath = xbmcaddon.Addon().getAddonInfo('path')
g_AddonName = xbmcaddon.Addon().getAddonInfo('name')
g_Args_URL = sys.argv[0]
# by changing MASO_ENABLED to 1 you express your consent with
# terms specified at www.roumenovomaso.cz
# zmenou premennej MASO_ENABLED na hodnotu 1 vyjadrujete suhlas
# s podmienkami popisanymi na www.roumenovomaso.cz
MASO_ENABLED = 0


def url2img_url(url, site='roumen'):
    if site in 'roumen':
        base = 'http://www.rouming.cz'
    else:
        base = 'http://www.roumenovomaso.cz/'
    image_url = re.search(r'.*?file=(.*)', url).group(1)
    return '%s/upload/%s' % (base, image_url)


def add_dir(name, url):
    li = xbmcgui.ListItem(name)
    xbmcplugin.addDirectoryItem(handle=g_AddonHandle,
                                url=url,
                                listitem=li,
                                isFolder=True)


def toggle(path):
    if path == 'archived':
        return 'upload'
    else:
        return 'archived'


# main()
base_url = 'http://www.rouming.cz'
maso_url = 'http://www.roumenovomaso.cz/?agree=on'
hp = HTMLParser()
intervals = ('today', 'week', 'month')
if len(sys.argv) > 2:
    mode = sys.argv[2][1:]
else:
    mode = None

print('Current mode: %s' % mode)

if not mode:
    add_dir('[COLOR red]GIFník[/COLOR]', '%s?%s' % (g_Args_URL, 'gifs1'))
    if MASO_ENABLED:
        add_dir('[COLOR red]MASO[/COLOR]', '%s?%s' % (g_Args_URL, 'maso'))
    add_dir('[COLOR yellow]Best of today[/COLOR]', '%s?%s' % (g_Args_URL, 'today'))
    add_dir('[COLOR yellow]Best of week[/COLOR]', '%s?%s' % (g_Args_URL, 'week'))
    add_dir('[COLOR yellow]Best of month[/COLOR]', '%s?%s' % (g_Args_URL, 'month'))

if mode in intervals:
    data = util.post(base_url, {'interval': intervals.index(mode)+1})
    data = util.substr(data, 'name="interval"', 'table')
    jpgs = re.findall(r'\?file=([^"]+)"', data)
    titles = re.findall(r' title="([^"]+)"', data)
    for title, jpg in zip(titles, jpgs):
        title = title.replace('&nbsp;', ' ')
        print(title, jpg)
        li = xbmcgui.ListItem(title)
        li.setInfo(type="image", infoLabels={})
        if mode == 'month':
            path = 'archived'
        else:
            path = 'upload'
        url = 'http://www.rouming.cz/%s/%s' % (path, jpg)
        if len(util.request(url)) < 5000:
            path = toggle(path)
        xbmcplugin.addDirectoryItem(handle=g_AddonHandle,
                                    url='http://www.rouming.cz/%s/%s' % (path,
                                                                         jpg),
                                    listitem=li,
                                    isFolder=False)
    xbmcplugin.endOfDirectory(g_AddonHandle)
elif 'gifs' in mode:
    page = int(mode.replace('gifs', ''))
    data = util.post(base_url + '/roumingGIFList.php',
                     {'page': page,
                      'submited': 1})
    print(page)
    data = util.substr(data, 'tbody', '</body>')
    urls = re.findall(r'(?:<source src="([^"]+\.(?:webm|mp4))".*?</video>|img src=\'([^  \']+)\')',
                      data,
                      re.S)
    urls = [''.join(x) for x in urls]
    titles = re.findall(r'(?:<video .+?title="([^"]*)")|(?:alt=\'([^\']+)\')',
                        data)
    print(urls, titles)
    titles = [''.join(x) for x in titles]
    for title, url in zip(titles, urls):
        title = hp.unescape(title)
        print(title, url)
        if '.gif' in url.split('/')[-1]:
            title += ' (GIF)'
        li = xbmcgui.ListItem(title)
        li.setInfo(type="video", infoLabels={})
        xbmcplugin.addDirectoryItem(handle=g_AddonHandle,
                                    url=url,
                                    listitem=li,
                                    isFolder=False)
    li = xbmcgui.ListItem('>> Next page')
    xbmcplugin.addDirectoryItem(handle=g_AddonHandle,
                                url='%s?%s%s' % (g_Args_URL,
                                                 'gifs',
                                                 page+1),
                                listitem=li,
                                isFolder=True)
    if page > 1:
        li = xbmcgui.ListItem('<< Previous page')
        xbmcplugin.addDirectoryItem(handle=g_AddonHandle,
                                    url='%s?%s%s' % (g_Args_URL,
                                                     'gifs',
                                                     page-1),
                                    listitem=li,
                                    isFolder=True)
    xbmcplugin.endOfDirectory(g_AddonHandle)
elif 'maso' in mode:
    data = util.parse_html(maso_url)
    for img in data.select('.masoList')[0].findAll('td', attrs={'align': None}):
        print(img)
        if not img.a:
            continue
        print(img)
        li = xbmcgui.ListItem(img.a.text)
        li.setInfo(type="image", infoLabels={})
        xbmcplugin.addDirectoryItem(handle=g_AddonHandle,
                                    url=url2img_url(img.a['href'],
                                                    site='maso'),
                                    listitem=li,
                                    isFolder=False)
    xbmcplugin.endOfDirectory(g_AddonHandle)
else:
    data = util.parse_html(base_url)
    for img in data.select('.roumingList')[0].select('td[width]'):
        print(img)
        li = xbmcgui.ListItem(img.a.text)
        li.setInfo(type="image", infoLabels={})
        xbmcplugin.addDirectoryItem(handle=g_AddonHandle,
                                    url=url2img_url(img.a['href']), listitem=li,
                                    isFolder=False)
    xbmcplugin.endOfDirectory(g_AddonHandle)
