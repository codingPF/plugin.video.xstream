# -*- coding: utf-8 -*-
from resources.lib import logger
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser

SITE_IDENTIFIER = 'pureanime'
SITE_NAME = 'Pureanime'
SITE_ICON = 'pureanime.png'
SITE_GLOBAL_SEARCH = False
URL_MAIN = 'https://pure-anime.net/'
URL_MOVIES = URL_MAIN + 'anime-movies/'
URL_SERIES = URL_MAIN + 'anime-serien/'
URL_TRENDING = URL_MAIN + 'trending/'
URL_SEARCH = URL_MAIN + '?s=%s'

def load():
    logger.info('Load %s' % SITE_NAME)
    params = ParameterHandler()
    params.setParam('sUrl', URL_SERIES)
    cGui().addFolder(cGuiElement('Anime Serien', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_MOVIES)
    cGui().addFolder(cGuiElement('Anime Movies/OVAs', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_TRENDING)
    cGui().addFolder(cGuiElement('Anime Trends', SITE_IDENTIFIER, 'showEntries'), params)
    cGui().addFolder(cGuiElement('Jahr', SITE_IDENTIFIER, 'showJahr'), params)
    cGui().addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    cGui().setEndOfDirectory()

def showJahr():
    params = ParameterHandler()
    sHtmlContent = cRequestHandler(URL_MAIN).request()
    pattern = 'class="releases.*?</nav>'
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)

    if isMatch:
        isMatch, aResult = cParser.parse(sHtmlContainer, 'href="([^"]+).*?>([^<]+)')
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
    oRequest = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False))
    sHtmlContent = oRequest.request()
    pattern = 'a[^>]title="([^"]+).*?href="([^"]+)'
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    if not isMatch:
        pattern = 'alt="([^"]+).*? href="([^"]+)"><div class="see">'
        isMatch, aResult = cParser().parse(sHtmlContent, pattern)

    if not isMatch:
        pattern = 'result-item.*?alt="([^"]+).*?href="([^"]+)">'
        isMatch, aResult = cParser().parse(sHtmlContent, pattern)

    if not isMatch:
        if not sGui: oGui.showInfo()
        return

    total = len(aResult)
    for sName, sUrl in aResult:
        isTvshow = True if 'serie' in sUrl else False
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showSeasons' if isTvshow else 'showHosters')
        params.setParam('entryUrl', sUrl)
        oGui.addFolder(oGuiElement, params, isTvshow, total)
    if not sGui:
        isMatchNextPage, sNextUrl = cParser().parseSingleResult(sHtmlContent, "<span class=[^>]current.*?href='([^']+)'[^>]class")
        if isMatchNextPage:
            params.setParam('sUrl', sNextUrl)
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
        oGui.setView('tvshows' if isTvshow else 'movies')
        oGui.setEndOfDirectory()

def showSeasons():
    params = ParameterHandler()
    entryUrl = params.getValue('entryUrl')
    sHtmlContent = cRequestHandler(entryUrl).request()
    pattern = "class='title'>Season[^>]([\d]+)"
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        cGui().showInfo()
        return

    isThumbnail, sThumbnail = cParser.parseSingleResult(sHtmlContent, 'poster.*?src="([^"]+)')
    total = len(aResult)
    for sSeasonNr in aResult:
        oGuiElement = cGuiElement("Staffel " + sSeasonNr, SITE_IDENTIFIER, 'showEpisodes')
        if isThumbnail:
            oGuiElement.setThumbnail(sThumbnail)
            oGuiElement.setFanart(sThumbnail)
        oGuiElement.setMediaType('season')
        oGuiElement.setSeason(sSeasonNr)
        params.setParam('sSeasonNr', int(sSeasonNr))
        cGui().addFolder(oGuiElement, params, True, total)
    cGui().setView('seasons')
    cGui().setEndOfDirectory()

def showEpisodes():
    params = ParameterHandler()
    entryUrl = params.getValue('entryUrl')
    sSeasonNr = params.getValue('sSeasonNr')
    sHtmlContent = cRequestHandler(entryUrl).request()
    pattern = "class='title'>Season[^>]%s.*?</li></ul>" % sSeasonNr
    isMatch, sContainer = cParser.parse(sHtmlContent, pattern)

    if isMatch:
        pattern = "numerando'>[^-]*-\s*(\d+)<.*?<a[^>]*href='([^']+)'>([^<]+)"
        isMatch, aResult = cParser.parse(sContainer[0], pattern)
    if not isMatch:
        cGui().showInfo()
        return

    isThumbnail, sThumbnail = cParser.parseSingleResult(sHtmlContent, 'poster.*?src="([^"]+)')
    total = len(aResult)
    for sEpisodeNr, sUrl, sName in aResult:
        oGuiElement = cGuiElement(sEpisodeNr + ' - ' + sName, SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setSeason(sSeasonNr)
        oGuiElement.setEpisode(sEpisodeNr)
        if isThumbnail:
            oGuiElement.setThumbnail(sThumbnail)
            oGuiElement.setFanart(sThumbnail)
        oGuiElement.setMediaType('episode')
        params.setParam('entryUrl', sUrl)
        cGui().addFolder(oGuiElement, params, False, total)
    cGui().setView('episodes')
    cGui().setEndOfDirectory()

def showHosters():
    hosters = []
    sUrl = ParameterHandler().getValue('entryUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    isMatch, aResult = cParser().parse(sHtmlContent, "data-type='([^']+).*?post='([^']+).*?nume='([^']+).*?class='title'>([^<]+).*?src='([^']+)")
    if isMatch:
        for sType, sPost, sNume, sName, sLang in aResult:
            oRequest = cRequestHandler('https://pure-anime.net/wp-admin/admin-ajax.php')
            oRequest.addParameters('action', 'doo_player_ajax')
            oRequest.addParameters('post', sPost)
            oRequest.addParameters('nume', sNume)
            oRequest.addParameters('type', sType)
            oRequest.setRequestType(1)
            sHtmlContent = oRequest.request()
            isMatch, sUrl = cParser.parseSingleResult(sHtmlContent, '(http[^"]+)')
            if 'cloudplayer' in sUrl:
                from resources.lib import jsunpacker
                import base64
                sHtmlContent = cRequestHandler(sUrl).request()
                isMatch, sUrl = cParser.parse(sHtmlContent, 'src":"([^"]+)')
                if isMatch:
                    sHtmlContent = cRequestHandler(sUrl[0], ignoreErrors=True).request()
                    isMatch, sUrl = cParser.parse(sHtmlContent, 'JuicyCodes.Run[^>]"(.*?)"[^>];')
                if isMatch:
                    sHtmlContent = base64.b64decode(sUrl[0].replace('"+"', ''))
                    isMatch, sUrl = cParser.parse(sHtmlContent, '(eval\(function\(p,a,c,k,e,d\).+)\s+?')
                if isMatch:
                    sHtmlContent = jsunpacker.unpack(sUrl[0])
                    isMatch, aResult = cParser.parse(sHtmlContent, 'file":"([^"]+).*?label":"([^"]+)')
                    for sUrl, sQualy in aResult:
                        hoster = {'link': sUrl, 'name': sName + Language(sLang) + sQualy}
                        hosters.append(hoster)
            if 'uniquestream' in sUrl:
                from resources.lib import jsunpacker
                import base64
                sHtmlContent = cRequestHandler(sUrl, ignoreErrors=True).request()
                isMatch, sUrl = cParser.parse(sHtmlContent, 'JuicyCodes.Run[^>]"(.*?)"[^>];')
                if isMatch:
                    sHtmlContent = base64.b64decode(sUrl[0].replace('"+"', ''))
                    isMatch, sUrl = cParser.parse(sHtmlContent, '(eval\(function\(p,a,c,k,e,d\).+)\s+?')
                if isMatch:
                    sHtmlContent = jsunpacker.unpack(sUrl[0])
                    isMatch, aResult = cParser.parse(sHtmlContent, 'file":"([^"]+).*?label":"([^"]+)')
                    for sUrl, sQualy in aResult:
                        hoster = {'link': sUrl, 'name': sName + Language(sLang) + sQualy}
                        hosters.append(hoster)
            else:
                hoster = {'link': sUrl, 'name': sName + Language(sLang)}
                hosters.append(hoster)
    if hosters:
        hosters.append('getHosterUrl')
    return hosters

def Language(sLang):
    if 'gersub' in sLang:
        return ' (Deutsche Untertitel) '
    elif 'engsub' in sLang:
        return ' (Englische Untertitel) '
    elif 'espsub' in sLang:
        return ' (Spanische Untertitel) '
    elif 'trsub' in sLang:
        return ' (Türkische Untertitel) '
    elif 'de.png' in sLang:
        return ' (Deutsch) '
    elif 'en.png' in sLang:
        return ' (Englische) '
    else:
        return ' '

def getHosterUrl(sUrl=False):
    if 'cloudplayer' in sUrl or 'uniquestream' in sUrl:
        return [{'streamUrl': sUrl, 'resolved': True}]
    else:
        return [{'streamUrl': sUrl, 'resolved': False}]

def showSearch():
    sSearchText = cGui().showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    cGui().setEndOfDirectory()

def _search(oGui, sSearchText):
    showEntries(URL_SEARCH % sSearchText, oGui, sSearchText)
