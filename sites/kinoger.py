# -*- coding: utf-8 -*-
from resources.lib import logger
from resources.lib.config import cConfig
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser

SITE_IDENTIFIER = 'kinoger'
SITE_NAME = 'Kinoger'
SITE_ICON = 'kinoger.png'
SITE_SETTINGS = '<setting default="kinoger.com" enable="!eq(-2,false)" id="kinoger-domain" label="30051" type="labelenum" values="kinoger.com|kinoger.to" />'
DOMAIN = cConfig().getSetting('kinoger-domain')
#URL_MAIN = 'https://' + DOMAIN
URL_MAIN = 'https://kinoger.to'
URL_SERIE = URL_MAIN + '/stream/serie/'


def load():
    logger.info("Load %s" % SITE_NAME)
    params = ParameterHandler()
    #geturl(URL_MAIN)
    params.setParam('sUrl', URL_MAIN)
    cGui().addFolder(cGuiElement('Filme & Serien', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_SERIE)
    cGui().addFolder(cGuiElement('Genre', SITE_IDENTIFIER, 'showGenre'))
    cGui().addFolder(cGuiElement('Serien', SITE_IDENTIFIER, 'showEntries'), params)
    cGui().addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    cGui().setEndOfDirectory()

def showGenre():
    params = ParameterHandler()
    sHtmlContent = cRequestHandler(URL_MAIN).request()
    pattern = '<li[^>]class="links"><a href="([^"]+).*?/>([^<]+)</a>'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        cGui().showInfo()
        return

    for sUrl, sName in aResult:
        params.setParam('sUrl', URL_MAIN + sUrl)
        cGui().addFolder(cGuiElement(sName, SITE_IDENTIFIER, 'showEntries'), params)
    cGui().setEndOfDirectory()


def showEntries(entryUrl=False, sGui=False, sSearchText=False):
    #geturl(URL_MAIN)
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False))
    if sSearchText:
        oRequest.addParameters('story', sSearchText)
        oRequest.addParameters('do', 'search')
        oRequest.addParameters('subaction', 'search')
        oRequest.addParameters('x', '0')
        oRequest.addParameters('y', '0')
        oRequest.addParameters('titleonly', '3')
        oRequest.addParameters('submit', 'submit')
    else:
        oRequest.addParameters('dlenewssortby', 'date')
        oRequest.addParameters('dledirection', 'desc')
        oRequest.addParameters('set_new_sort', 'dle_sort_main')
        oRequest.addParameters('set_direction_sort', 'dle_direction_main')
    oRequest.setRequestType(1)
    sHtmlContent = oRequest.request()
    pattern = 'class="title.*?href="([^"]+)">([^<]+).*?src="([^"]+)(.*?)</span>'
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)

    if not isMatch:
        if not sGui: oGui.showInfo()
        return

    cf = cRequestHandler.createUrl(entryUrl, oRequest)
    total = len(aResult)
    for sUrl, sName, sThumbnail, sDummy in aResult:
        if sSearchText and not cParser().search(sSearchText, sName):
            continue
        sThumbnail = sThumbnail + cf
        isTvshow = True if 'staffel' in sName.lower() else False
        isYear, sYear = cParser.parse(sName, "(.*?)\((\d*)\)")
        for name, year in sYear:
            sName = name
            sYear = year
            break
        isDesc, sDesc = cParser.parseSingleResult(sDummy, '</b>([^"]+)</div>')
        isDuration, sDuration = cParser.parseSingleResult(sDummy, '[Laufzeit][Spielzeit]:[^>]([\d]+)')
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showSeasons' if isTvshow else 'showHosters')
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setFanart(sThumbnail)
        if isYear:
            oGuiElement.setYear(sYear)
        if isDesc:
            oGuiElement.setDescription(sDesc)
        if isDuration:
            oGuiElement.addItemValue('duration', sDuration)
        oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
        params.setParam('sThumbnail', sThumbnail)
        params.setParam('TVShowTitle', sName)
        params.setParam('entryUrl', sUrl)
        oGui.addFolder(oGuiElement, params, isTvshow, total)
    if not sGui:
        isMatchNextPage, sNextUrl = cParser().parseSingleResult(sHtmlContent, '<a[^>]href="([^"]+)">vorw')
        if isMatchNextPage:
            params.setParam('sUrl', sNextUrl)
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
        oGui.setView('tvshows' if 'staffel' in sName.lower() else 'movies')
        oGui.setEndOfDirectory()

def showSeasons():
    #geturl(URL_MAIN)
    params = ParameterHandler()
    entryUrl = params.getValue('entryUrl')
    sThumbnail = params.getValue('sThumbnail')
    sTVShowTitle = params.getValue('TVShowTitle')
    sHtmlContent = cRequestHandler(entryUrl).request()
    pattern = 'sst.show.*?</script>'
    isMatch, sContainer = cParser.parseSingleResult(sHtmlContent, pattern)

    if isMatch:
        pattern = "'([^\]]+)"
        isMatch, aResult = cParser.parse(sContainer, pattern)
    if not isMatch:
        cGui().showInfo()
        return

    i = 0
    isDesc, sDesc = cParser.parseSingleResult(sHtmlContent, '</b>([^"]+)<br><br>')
    total = len(aResult)
    for sSeasonNr in aResult:
        i = i + 1
        oGuiElement = cGuiElement('Staffel ' + str(i), SITE_IDENTIFIER, 'showEpisodes')
        oGuiElement.setTVShowTitle(sTVShowTitle)
        oGuiElement.setSeason(i)
        if sThumbnail:
            oGuiElement.setThumbnail(sThumbnail)
            oGuiElement.setFanart(sThumbnail)
        if isDesc:
            oGuiElement.setDescription(sDesc)
        params.setParam('sNr', i)
        params.setParam('sSeasonNr', sSeasonNr)
        cGui().addFolder(oGuiElement, params, True, total)
    cGui().setView('seasons')
    cGui().setEndOfDirectory()


def showEpisodes():
    params = ParameterHandler()
    entryUrl = params.getValue('entryUrl')
    sHtmlContent = cRequestHandler(entryUrl).request()
    sEpisodeNr = params.getValue('sSeasonNr')
    sNr = params.getValue('sNr')
    sThumbnail = params.getValue('sThumbnail')
    sTVShowTitle = params.getValue('TVShowTitle')
    pattern = "(http[^']+)"
    isMatch, aResult = cParser.parse(sEpisodeNr, pattern)

    if not isMatch:
        cGui().showInfo()
        return

    i = 0
    isDesc, sDesc = cParser.parseSingleResult(sHtmlContent, '</b>([^"]+)<br><br>')
    total = len(aResult)
    for sEpisodeNr in aResult:
        i = i + 1
        oGuiElement = cGuiElement('Episode ' + str(i), SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setTVShowTitle(sTVShowTitle)
        oGuiElement.setSeason(sNr)
        oGuiElement.setEpisode(i)
        if isDesc:
            oGuiElement.setDescription(sDesc)
        if sThumbnail:
            oGuiElement.setThumbnail(sThumbnail)
            oGuiElement.setFanart(sThumbnail)
        params.setParam('entryUrl', sEpisodeNr)
        cGui().addFolder(oGuiElement, params, False, total)
    cGui().setView('episodes')
    cGui().setEndOfDirectory()


def showHosters():
    hosters = []
    sUrl = ParameterHandler().getValue('entryUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    pattern = "show[^>]\d,[^>][^>]'([^']+)"
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    if isMatch:
        for sUrl in aResult:
            if 'sst' in sUrl:
                oRequest = cRequestHandler(sUrl)
                oRequest.addHeaderEntry('Referer', sUrl)
                sHtmlContent = oRequest.request()
                pattern = 'file:"(.*?)"'
                isMatch, sContainer = cParser.parseSingleResult(sHtmlContent, pattern)
                pattern = '(http[^",]+)'
                isMatch, aResult = cParser().parse(sContainer[0], pattern)
                for sUrl in aResult:
                    hoster = {'link': sUrl, 'name': Qualy2(sUrl)}
                    hosters.append(hoster)
            if 'kinoger.re' in sUrl:
                oRequest = cRequestHandler(sUrl.replace('/v/', '/api/source/'))
                oRequest.addHeaderEntry('Referer', sUrl)
                oRequest.addParameters('r', 'https://kinoger.com/')
                oRequest.addParameters('d', 'kinoger.re')
                sHtmlContent = oRequest.request()
                pattern = 'file":"([^"]+)","label":"([^"]+)'
                isMatch, aResult = cParser.parse(sHtmlContent, pattern)
                for sUrl, sQualy in aResult:
                    hoster = {'link': sUrl, 'name': sQualy}
                    hosters.append(hoster)
            if 'cloudvideo.tv' in sUrl:
                oRequest = cRequestHandler(sUrl.replace('emb.html?','embed-') + '.html')
                oRequest.addHeaderEntry('Referer', sUrl)
                sHtmlContent = oRequest.request()
                pattern = 'source src="([^"]+)'
                isMatch, aResult = cParser.parseSingleResult(sHtmlContent, pattern)
                oRequest = cRequestHandler(aResult)
                oRequest.addHeaderEntry('Referer', sUrl)
                sHtmlContent = oRequest.request()

                pattern = 'RESOLUTION=\d+x([\d]+).*?CODECS=".*?(http[^#]+)'
                isMatch, aResult = cParser().parse(sHtmlContent, pattern)
                for sQualy, sUrl in aResult:
                    if not 'iframe' in sUrl:
                        hoster = {'link': sUrl, 'name': sQualy}
                        hosters.append(hoster)
    elif 'hdgo' in sUrl or 'sst' in sUrl:
        oRequest = cRequestHandler(sUrl)
        oRequest.addHeaderEntry('Referer', sUrl)
        sHtmlContent = oRequest.request()
        pattern = 'file:"(.*?)"'
        isMatch, sContainer = cParser.parseSingleResult(sHtmlContent, pattern)
        pattern = '(http[^",]+)'
        isMatch, aResult = cParser().parse(sContainer[0], pattern)
        for sUrl in aResult:
            hoster = {'link': sUrl, 'name': Qualy2(sUrl)}
            hosters.append(hoster)
    if hosters:
        hosters.append('getHosterUrl')
    return hosters

def getHosterUrl(sUrl=False):
    if sUrl.startswith('//'):
        sUrl = 'https:' + sUrl
    if 'sst' in sUrl:
        return [{'streamUrl': sUrl, 'resolved': True}]
    else:
        return [{'streamUrl': sUrl + '|Referer=' + sUrl + '&Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0', 'resolved': True}]

def showSearch():
    oGui = cGui()
    sSearchText = oGui.showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    oGui.setEndOfDirectory()

def _search(oGui, sSearchText):
    #geturl(URL_MAIN)
    showEntries(URL_MAIN, oGui, sSearchText)

def Qualy2(sUrl):
    if '360p' in sUrl:
        return '360p'
    elif '480p' in sUrl:
        return '480p'
    elif '720p' in sUrl:
        return '720p'
    else:
        return '1080p'

def geturl(sUrl):
    from urlparse import urlparse
    import urllib2, cookielib, base64
    try:
        cj = cookielib.CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0')]
        response = opener.open(sUrl)
    except urllib2.HTTPError as e:
        if e.code == 403:
            data = e.fp.read()
            if 'DDOS-GUARD' in data:
                pattern = 'action="([^"]+)'
                isMatch, sUrl = cParser.parseSingleResult(data, pattern)
                url = e.geturl()
                parsed_url = urlparse(url)
                if  parsed_url.path == '':
                    u = base64.b64encode('/')
                else:
                    u = base64.b64encode(parsed_url.path)
                h = parsed_url.scheme + '://' + parsed_url.netloc
                h = base64.b64encode(h)
                oRequest = cRequestHandler('https:' + sUrl, caching=False, ignoreErrors=True)
                oRequest.addHeaderEntry('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0')
                oRequest.addHeaderEntry('Referer', 'https://kinoger.com/')
                oRequest.addHeaderEntry('Upgrade-Insecure-Requests', '1')
                oRequest.addHeaderEntry('Origin', 'https://kinoger.com')
                oRequest.addParameters('u', u)
                oRequest.addParameters('h', h)
                oRequest.addParameters('p', '')
                oRequest.request()
                sUrl = oRequest.getRealUrl()
                sHtmlContent = cRequestHandler(URL_MAIN).request()
                return sHtmlContent
