# -*- coding: utf-8 -*-
from resources.lib import logger
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser

SITE_IDENTIFIER = 'flimmerstube_com'
SITE_NAME = 'Flimmerstube'
SITE_ICON = 'flimmerstube.png'
URL_MAIN = 'http://flimmerstube.com'
URL_MOVIE = URL_MAIN + '/video/vic/alle_filme'
URL_SEARCH = URL_MAIN + '/video/shv'

def load():
    logger.info("Load %s" % SITE_NAME)
    params = ParameterHandler()
    params.setParam('sUrl', URL_MOVIE)
    cGui().addFolder(cGuiElement('Deutsche Horrorfilme', SITE_IDENTIFIER, 'showEntries'), params)
    cGui().addFolder(cGuiElement('Genre', SITE_IDENTIFIER, 'showGenre'), params)
    cGui().addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    cGui().setEndOfDirectory()

def showGenre():
    params = ParameterHandler()
    entryUrl = params.getValue('sUrl')
    sHtmlContent = cRequestHandler(entryUrl).request()
    pattern = '<a[^>]class=[^>]catName[^>][^>]href="([^"]+)"[^>]>([^"]+)</a>'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        cGui().showInfo()
        return

    for sUrl, sName in aResult:
        params.setParam('sUrl', URL_MAIN + sUrl)
        cGui().addFolder(cGuiElement(sName, SITE_IDENTIFIER, 'showEntries'), params)
    cGui().setEndOfDirectory()

def showEntries(entryUrl=False, sGui=False, sSearchText=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False))
    if sSearchText:
        oRequest.addHeaderEntry('Referer', entryUrl)
        oRequest.addHeaderEntry('Upgrade-Insecure-Requests', '1')
        oRequest.addParameters('query', sSearchText)
        if '+' in sSearchText:
            oRequest.addParameters('c', '70')
        else:
            oRequest.addParameters('c', '')
        oRequest.setRequestType(1)
    sHtmlContent = oRequest.request()
    pattern = 've-screen.*?title="([^"]+).*?url[^>]([^")]+).*?href="([^">]+)'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        if not sGui: oGui.showInfo()
        return

    total = len(aResult)
    for sName, sThumbnail, sUrl in aResult:
        if sSearchText and not cParser().search(sSearchText, sName):
            continue
        isMatch, sYear = cParser.parse(sName, "(.*?)\((\d{4})\)")
        for name, year in sYear:
            sName = name
            sYear = year
            break

        if sThumbnail.startswith('/'):
            sThumbnail = URL_MAIN + sThumbnail
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showHosters')
        if sYear:
            oGuiElement.setYear(sYear)
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setFanart(sThumbnail)
        params.setParam('entryUrl', URL_MAIN + sUrl)
        oGui.addFolder(oGuiElement, params, False, total)
    if not sGui:
        pattern = "spages[^>][^>]([^']+)[^>][^>];return[^>]false;[^>]><span>&raquo;.*?location.href = '([^']+)"
        aResult = cParser().parse(sHtmlContent, pattern)
        if aResult[0] and aResult[1][0]:
            for sNr, Url in aResult[1]:
                params.setParam('sUrl', URL_MAIN + Url + sNr)
                oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
        oGui.setView('movies')
        oGui.setEndOfDirectory()

def showHosters():
    hosters = []
    params = ParameterHandler()
    sUrl = params.getValue('entryUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    pattern = "src=[^>]'([^']+)'\s"
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    if not isMatch:
        pattern = 'src=[^>]"(http[^"]+)'
        isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    if isMatch:
        for sUrl in aResult:
            hoster = {'link': sUrl, 'name': sUrl}
            hosters.append(hoster)
    if hosters:
        hosters.append('getHosterUrl')
    return hosters

def getHosterUrl(sUrl=False):
    if 'youtube' in sUrl:
        import xbmc, xbmcgui
        if not xbmc.getCondVisibility("System.HasAddon(%s)" % "plugin.video.youtube"):
            xbmc.executebuiltin("InstallAddon(%s)" % "plugin.video.youtube")
    return [{'streamUrl': sUrl, 'resolved': False}]

def showSearch():
    sSearchText = cGui().showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    cGui().setEndOfDirectory()


def _search(oGui, sSearchText):
    showEntries(URL_SEARCH, oGui, sSearchText)
