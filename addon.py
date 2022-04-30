# -*- coding: utf-8 -*-
# plugin for viewing pics on rouming.cz on kodi. browsing archive
# is currently not supported

import bs4
import re
import requests
import sys
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

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
        base = 'https://www.rouming.cz'
    else:
        base = 'https://www.roumenovomaso.cz/'
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
base_url = 'https://www.rouming.cz'
maso_url = 'https://www.roumenovomaso.cz/?agree=on'
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
    soup = bs4.BeautifulSoup(requests.post(f'{base_url}/roumingListTop.php', {'interval': intervals.index(mode)+1}).text, features="html.parser")
    for title, jpg in [(x.text, x['href']) for x in soup.select('td > a') if 'roumingShow.php' in x['href']]:
        jpg = re.match(r'roumingShow.php\?file=(.*)', jpg).group(1)
        print(title, jpg)
        li = xbmcgui.ListItem(title)
        li.setInfo(type="image", infoLabels={})
        if mode == 'month':
            path = 'archived'
        else:
            path = 'upload'

        url = 'https://www.rouming.cz/%s/%s' % (path, jpg)
        if requests.get(url).status_code != 200:
            path = toggle(path)
        xbmcplugin.addDirectoryItem(handle=g_AddonHandle,
                                    url='https://www.rouming.cz/%s/%s' % (path,
                                                                         jpg),
                                    listitem=li,
                                    isFolder=False)
    xbmcplugin.endOfDirectory(g_AddonHandle)
elif 'gifs' in mode:
    page = int(mode.replace('gifs', ''))
    soup = requests.post(f'{base_url}/roumingGIFList.php', {'page': page, 'submited': 1})
    print(f'page: {page}')
    urls = re.findall(r'(?:<source src="([^"]+\.(?:webm|mp4))".*?</video>|img src=\'([^  \']+)\')',
                      soup.text,
                      re.S)
    urls = [''.join(x) for x in urls]
    titles = re.findall(r'(?:<video .+?title="([^"]*)")|(?:alt=\'([^\']+)\')',
                        soup.text)
    print(urls, titles)
    titles = [''.join(x) for x in titles]
    for title, url in zip(titles, urls):
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
    soup = bs4.BeautifulSoup(requests.get(maso_url).text, features="html.parser")
    for img in soup.select('.masoList')[0].findAll('td', attrs={'align': None}):
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
    data = bs4.BeautifulSoup(requests.get(base_url).text, features="html.parser")
    for img in data.select('.roumingList .mw700 table')[0].select('td[width]'):
        li = xbmcgui.ListItem(img.a.text)
        li.setInfo(type="image", infoLabels={})
        xbmcplugin.addDirectoryItem(handle=g_AddonHandle,
                                    url=url2img_url(img.a['href']), listitem=li,
                                    isFolder=False)
    xbmcplugin.endOfDirectory(g_AddonHandle)
