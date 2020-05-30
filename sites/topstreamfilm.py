# -*- coding: utf-8 -*-
from resources.lib import logger
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler2 import cRequestHandler
from resources.lib.parser import cParser

SITE_IDENTIFIER = 'topstreamfilm'
SITE_NAME = 'Topstreamfilm'
SITE_ICON = 'topstreamfilm.png'
URL_MAIN = 'https://topstreamfilm.com/'
URL_MOVIES = URL_MAIN + 'filme'
URL_SHOWS = URL_MAIN + 'serien'
URL_POPULAR = URL_MAIN + 'beliebte-filme-serien'
URL_SEARCH = URL_MAIN + '?s=%s'

def load():
    logger.info("Load %s" % SITE_NAME)
    params = ParameterHandler()
    params.setParam('sUrl', URL_MOVIES)
    cGui().addFolder(cGuiElement('Filme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_SHOWS)
    cGui().addFolder(cGuiElement('Serien', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_POPULAR)
    cGui().addFolder(cGuiElement('Beliebte', SITE_IDENTIFIER, 'showEntries'), params)
    cGui().addFolder(cGuiElement('Genre', SITE_IDENTIFIER, 'showGenre'), params)
    cGui().addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    cGui().setEndOfDirectory()

def showGenre():
    params = ParameterHandler()
    sHtmlContent = cRequestHandler(URL_MAIN).request()
    pattern = 'Kategorien.*?</aside>'
    isMatch, sContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if  isMatch:
        pattern = 'href="([^"]+).*?>([^<]+)'
        isMatch, aResult = cParser.parse(sContainer, pattern)
    if not isMatch:
        cGui().showInfo()
        return

    for sUrl, sName in aResult:
        params.setParam('sUrl', sUrl)
        cGui().addFolder(cGuiElement(sName, SITE_IDENTIFIER, 'showEntries'), params)
    cGui().setEndOfDirectory()

def showEntries(entryUrl=False, sGui=False, sSearchText=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl)
    sHtmlContent = oRequest.request()
    pattern = 'TPost C">.*?href="([^"]+).*?img[^>]src="([^"]+)(.*?)Title">([^<]+)(.*?)Description">([^"]+)</p>'
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    if not isMatch:
        if not sGui: oGui.showInfo()
        return

    cf = cRequestHandler.createUrl(entryUrl, oRequest)
    total = len(aResult)
    for sUrl, sThumbnail, sType, sName, sDummy, sDesc in aResult:
        isDuration, sDuration = cParser.parseSingleResult(sDummy, 'time">([\d(h) \d]+)')
        isYear, sYear = cParser.parseSingleResult(sDummy, 'date_range">([\d]+)')
        sThumbnail = 'https:' + sThumbnail + cf
        if sSearchText and not cParser().search(sSearchText, sName):
            continue
        isTvshow = True if 'Season' in sType or 'TV' in sType else False
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showSeasons' if isTvshow else 'showHosters')
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setFanart(sThumbnail)
        oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
        if isDuration:
            oGuiElement.addItemValue('duration', int(sDuration.replace('h ', '')) - 40)
        if isYear:
            oGuiElement.setYear(sYear)
        oGuiElement.setDescription(sDesc)
        params.setParam('entryUrl', sUrl)
        params.setParam('sThumbnail', sThumbnail)
        oGui.addFolder(oGuiElement, params, isTvshow, total)
    if not sGui:
        pattern = 'next page-numbers" href="([^"]+)'
        isMatchNextPage, sNextUrl = cParser.parseSingleResult(sHtmlContent, pattern)
        if isMatchNextPage:
            params.setParam('sUrl', sNextUrl)
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
        oGui.setView('tvshow' if 'Season' in sType or 'TV' in sType else 'movie')
        oGui.setEndOfDirectory()

def showSeasons():
    params = ParameterHandler()
    entryUrl = params.getValue('entryUrl')
    sHtmlContent = cRequestHandler(entryUrl).request()
    isMatch, aResult = cParser.parse(sHtmlContent, 'Season <span>([\d]+)')
    if not isMatch:
        cGui().showInfo()
        return

    isDesc, sDesc = cParser.parseSingleResult(sHtmlContent, 'class="Description">(.*?)</p>')
    total = len(aResult)
    for sSeason, in aResult:
        oGuiElement = cGuiElement('Staffel ' + sSeason, SITE_IDENTIFIER, 'showEpisodes')
        oGuiElement.setMediaType('season')
        oGuiElement.setSeason(sSeason)
        oGuiElement.setThumbnail(params.getValue('sThumbnail'))
        oGuiElement.setFanart(params.getValue('sThumbnail'))
        if isDesc:
            oGuiElement.setDescription(sDesc)
        params.setParam('Season', sSeason)
        cGui().addFolder(oGuiElement, params, True, total)
    cGui().setView('seasons')
    cGui().setEndOfDirectory()

def showEpisodes():
    params = ParameterHandler()
    entryUrl = params.getValue('entryUrl')
    sSeason = params.getValue('Season')
    sHtmlContent = cRequestHandler(entryUrl).request()
    pattern = 'Season <span>%s.*?></tbody>' % sSeason
    isMatch, sContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if isMatch:
        pattern = 'Num">([\d]+).*?href="([^"]+)'
        isMatch, aResult = cParser.parse(sContainer, pattern)
    if not isMatch:
        cGui().showInfo()
        return

    isDesc, sDesc = cParser.parseSingleResult(sHtmlContent, 'class="Description">(.*?)</p>')
    total = len(aResult)
    for sEpisode, sUrl in aResult:
        oGuiElement = cGuiElement('Folge ' + sEpisode, SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setMediaType('season')
        oGuiElement.setSeason(sSeason)
        oGuiElement.setEpisode(sEpisode)
        oGuiElement.setMediaType('episode')
        oGuiElement.setThumbnail(params.getValue('sThumbnail'))
        if isDesc:
            oGuiElement.setDescription(sDesc)
        oGuiElement.setFanart(params.getValue('sThumbnail'))
        params.setParam('entryUrl', sUrl)
        cGui().addFolder(oGuiElement, params, False, total)
    cGui().setView('episodes')
    cGui().setEndOfDirectory()

def showHosters():
    hosters = []
    sHtmlContent = cRequestHandler(ParameterHandler().getValue('entryUrl'), ignoreErrors=True).request()
    pattern = 'class="TPlayer">.*?class="btnsplyr'
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    sHtmlContainer = sHtmlContainer.replace('&quot;', '"')
    isMatch, aResult = cParser().parse(sHtmlContainer, '(http[^"]+)')
    for sUrl2 in aResult:
        sHtmlContent = cRequestHandler(sUrl2, ignoreErrors=True).request()
        pattern = '" src="([^"]+)"'
        isMatch, sUrl3 = cParser().parseSingleResult(sHtmlContent, pattern)
        if 'topstreamfilm' in sUrl3:
            sUrl3 = sUrl3[:-1]
            oRequest = cRequestHandler(sUrl3, ignoreErrors=True)
            oRequest.addHeaderEntry('Referer', sUrl3)
            oRequest.addHeaderEntry('Upgrade-Insecure-Requests', '1')
            sHtmlContent = oRequest.request()
            pattern = "var id = trde[^>]'([^']+)"
            isMatch, sId = cParser().parseSingleResult(sHtmlContent, pattern)
            if isMatch:
                pattern = "iframe.src = '([^']+)"
                isMatch, sUrl4 = cParser().parseSingleResult(sHtmlContent, pattern)
            if isMatch:
                oRequest = cRequestHandler(sUrl4 + sId[::-1], caching=False, ignoreErrors=True)
                oRequest.addHeaderEntry('Referer', sUrl4)
                oRequest.addHeaderEntry('Upgrade-Insecure-Requests', '1')
                sHtmlContent = oRequest.request()
                sUrl6 = oRequest.getRealUrl()
                if 'public' in sUrl6:
                    sUrl6 = sUrl6.replace('public/dist/index.html?id=', 'getLinkStreamMd5/')
                    oRequest = cRequestHandler(sUrl6, ignoreErrors=True)
                    oRequest.addHeaderEntry('Referer', sUrl4)
                    oRequest.addHeaderEntry('Upgrade-Insecure-Requests', '1')
                    sHtmlContent = oRequest.request()
                    isMatch, aResult = cParser().parse(sHtmlContent, 'file":"([^"]+).*?label":"([^"]+)')
                    if isMatch:
                        for sUrl, sQ in aResult:
                            hoster = {'link': sUrl, 'name': sQ}
                            hosters.append(hoster)
        if 'club' in sUrl3:
            oRequest = cRequestHandler(sUrl3, ignoreErrors=True)
            oRequest.addHeaderEntry('Referer', URL_MAIN)
            oRequest.addHeaderEntry('Upgrade-Insecure-Requests', '1')
            sHtmlContent = oRequest.request()
            isMatch, sUrl7 = cParser().parseSingleResult(sHtmlContent, 'iframe[^>]src="([^"]+)')
            if isMatch:
                oRequest = cRequestHandler(sUrl7, caching=False, ignoreErrors=True)
                oRequest.addHeaderEntry('Referer', 'https://topstreamfilm.com/')
                oRequest.addHeaderEntry('X-Requested-With', 'XMLHttpRequest')
                oRequest.request()
                sUrl8 = oRequest.getRealUrl()
                oRequest = cRequestHandler(sUrl8.replace('v', 'api/source'), ignoreErrors=True)
                oRequest.addHeaderEntry('Referer', sUrl8)
                oRequest.addHeaderEntry('X-Requested-With', 'XMLHttpRequest')
                oRequest.addHeaderEntry('Origin', 'https://feurl.com')
                oRequest.addParameters('r', 'https://fd.topsf.club/')
                oRequest.addParameters('d', 'feurl.com')
                oRequest.setRequestType(1)
                sHtmlContent = oRequest.request()
            pattern = 'file":"([^"]+)","label":"([^"]+)'
            isMatch, aResult = cParser().parse(sHtmlContent, pattern)
            if isMatch:
                for sUrl, sQ in aResult:
                    hoster = {'link': sUrl, 'name': sQ}
                    hosters.append(hoster)
    if hosters:
        hosters.append('getHosterUrl')
    return hosters

def _redirectHoster(url):
    import urllib2
    opener = urllib2.build_opener()
    opener.addheaders = [('Referer', url)]
    opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0')]
    try:
        resp = opener.open(url)
        if url != resp.geturl():
            return resp.geturl()
        else:
            return url
    except urllib2.HTTPError, e:
        if e.code == 403:
            if url != e.geturl():
                return e.geturl()
        raise

def getHosterUrl(sUrl=False):
    if 'fvs.io' in sUrl:
        sUrl = _redirectHoster(sUrl)
    return [{'streamUrl': sUrl, 'resolved': True}]

def showSearch():
    sSearchText = cGui().showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    cGui().setEndOfDirectory()

def _search(oGui, sSearchText):
    showEntries(URL_SEARCH % sSearchText, oGui, sSearchText)
