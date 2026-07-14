# -*- coding: utf-8 -*-
# plugin for viewing pics on rouming.cz on kodi. browsing archive
# is currently not supported

import bs4
import html
import re
import requests
import sys
import urllib.parse
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


def get_object_id(key, kind='file'):
    if kind == 'gif':
        resp = requests.get('%s/roumingGIF.php' % base_url, params={'gif': key})
    else:
        resp = requests.get('%s/roumingShow.php' % base_url, params={'file': key})
    m = re.search(r'roumingComments\.php\?object=(\d+)', resp.text)
    return m.group(1) if m else None


def fetch_comments(key, kind='file'):
    object_id = get_object_id(key, kind)
    if not object_id:
        return None
    soup = bs4.BeautifulSoup(
        requests.get('%s/roumingComments.php' % base_url, params={'object': object_id}).text,
        features="html.parser")
    comments = []
    for header in soup.select('tr.roumingForum'):
        title_tds = header.select('td.roumingForumTitle')
        info_td = title_tds[1] if len(title_tds) > 1 else title_tds[0]
        font_tag = info_td.find('font')
        date = font_tag.get_text(strip=True).strip('()') if font_tag else ''
        a_tag = info_td.find('a')
        if a_tag:
            a_tag.extract()
        if font_tag:
            font_tag.extract()
        nick = info_td.get_text(strip=True).strip('()') or 'Anonym'
        message_row = header.find_next_sibling('tr')
        message_td = message_row.find('td', class_='roumingForumMessage') if message_row else None
        message = message_td.get_text(strip=True) if message_td else ''
        comments.append('%s (%s)\n%s' % (nick, date, message))
    return comments


def show_comments(key, kind='file'):
    comments = fetch_comments(key, kind)
    if not comments:
        xbmcgui.Dialog().notification(g_AddonName, 'Žiadne komentáre', xbmcgui.NOTIFICATION_INFO)
        return
    xbmcgui.Dialog().textviewer('Komentáre: %s' % key, '\n\n'.join(comments))


def add_comments_context(li, key, kind='file'):
    url = '%s?%s' % (g_Args_URL, 'comments' + kind[0] + urllib.parse.quote(key, safe=''))
    li.addContextMenuItems([('Komentáre', 'RunPlugin(%s)' % url)])


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
        add_comments_context(li, jpg)
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
    titles = [html.unescape(''.join(x)) for x in titles]
    gif_ids = re.findall(r'<a name="(\d+)"></a>', soup.text)
    for title, url, gif_id in zip(titles, urls, gif_ids):
        print(title, url)
        if '.gif' in url.split('/')[-1]:
            title += ' (GIF)'
        li = xbmcgui.ListItem(title)
        li.setInfo(type="video", infoLabels={})
        add_comments_context(li, gif_id, kind='gif')
        xbmcplugin.addDirectoryItem(handle=g_AddonHandle,
                                    url=url,
                                    listitem=li,
                                    isFolder=False)
    li = xbmcgui.ListItem('[COLOR yellow]>> Next page[/COLOR]')
    xbmcplugin.addDirectoryItem(handle=g_AddonHandle,
                                url='%s?%s%s' % (g_Args_URL,
                                                 'gifs',
                                                 page+1),
                                listitem=li,
                                isFolder=True)
    if page > 1:
        li = xbmcgui.ListItem('[COLOR yellow]<< Previous page[/COLOR]')
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
elif mode.startswith('comments'):
    rest = mode[len('comments'):]
    kind = 'gif' if rest[0] == 'g' else 'file'
    show_comments(urllib.parse.unquote(rest[1:]), kind=kind)
else:
    data = bs4.BeautifulSoup(requests.get(base_url).text, features="html.parser")
    for img in data.select('.roumingList .mw700 table')[0].select('td[width]'):
        li = xbmcgui.ListItem(img.a.text)
        li.setInfo(type="image", infoLabels={})
        add_comments_context(li, re.search(r'.*?file=(.*)', img.a['href']).group(1))
        xbmcplugin.addDirectoryItem(handle=g_AddonHandle,
                                    url=url2img_url(img.a['href']), listitem=li,
                                    isFolder=False)
    xbmcplugin.endOfDirectory(g_AddonHandle)
