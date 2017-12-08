# plugin for viewing pics on rouming.cz on kodi. browsing archive
# is currently not supported

import re
import sys
import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin
import util

g_AddonHandle = int(sys.argv[1])
g_AddonPath = xbmcaddon.Addon().getAddonInfo('path')
g_AddonName = xbmcaddon.Addon().getAddonInfo('name')
g_Args_URL = sys.argv[0]


def url2img_url(url):
    image_url = re.search(r'.*?file=(.*)', url).group(1)
    return 'http://www.rouming.cz/upload/%s' % image_url


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
intervals = ('today', 'week', 'month')
if len(sys.argv) > 2:
    mode = sys.argv[2][1:]
else:
    mode = None

print('Current mode: %s' % mode)

if not mode:
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
else:
    data = util.parse_html(base_url)
    for img in data.select_one('.roumingList').select('td[width]'):
        print(img)
        li = xbmcgui.ListItem(img.a.text)
        li.setInfo(type="image", infoLabels={})
        xbmcplugin.addDirectoryItem(handle=g_AddonHandle,
                                    url=url2img_url(img.a['href']), listitem=li,
                                    isFolder=False)
    xbmcplugin.endOfDirectory(g_AddonHandle)
