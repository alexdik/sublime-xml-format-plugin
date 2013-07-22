# Description:
#    This plugin implements intelligent xml alignment (indentation) to make big
#    xml files easily readable by human. The plugin keeps original xml data so  
#    source and indented xmls are equal.
# 
# Functionality:
#    After executing alignment there 2 possible results:
#    1) If xml is invalid there would be printed error description in status bar.
#    2) If xml is valid it would be successfully formatted and there would be
#       printed time taken for execution is status bar.
#
# Installation:
#    Just copy this file to ./sublime/Data/Packages/Default
#    To enable formatting hotkey, add following string to 
#    Preferences -> Key Bindings - User:
#    { "keys": ["ctrl+shift+x"], "command": "xml_format" }

import sublime, sublime_plugin
import re, time
from xml.dom.minidom import parseString

class XmlFormatCommand(sublime_plugin.TextCommand):
	def run(self, edit):		
		flen = self.view.size()

		xml = self.view.substr(sublime.Region(0, flen))
		
		try:
			dom = parseString(xml)			
		except Exception as e:
			sublime.status_message('Xml is invalid: ' + e.args[0])
		else:
			startTime = time.time()

			xml = removeLayout(xml)
			xml = addLayout(xml)

			self.view.erase(edit, sublime.Region(0, flen))
			self.view.insert(edit, 0, xml)

			endTime = time.time()
			ms = str(int((endTime - startTime)*1000))
			sublime.status_message('Alignment completed. Processing time: ' + ms + 'ms')

def getNextToken(str, strt, lenStr):
	if strt >= lenStr:
		return None

	buf = ''
	pos = strt
	attr = False;

	isComment = isCDATA = isText = isTag = False
	if lenStr > strt + 2 and str[strt:strt+2] == '<!':
		isComment = lenStr > strt+4 and str[strt:strt+4] == '<!--'
		if not isComment:
			isCDATA = lenStr > strt+9 and str[strt:strt+9] == '<![CDATA['
	else:
		isText = str[strt] != '<'
		isTag = not isText
	
	if isTag:
		while pos < lenStr:
			chr = str[pos]

			if chr =='"':
				attr = not attr

			if chr !='\r' and chr !='\n':
				buf += chr
			else:
				buf += ' '

			if chr == '>' and not attr:
				break
			
			pos += 1
	elif isText:
		while pos < lenStr:
			chr = str[pos]

			if chr == '<':
				break

			buf += chr
			pos += 1
	elif isComment:
		pos += 4
		while pos < lenStr:
			if str[pos:pos+3] == '-->':
				buf = '<!--' + buf + '-->'
				break

			chr = str[pos]
			buf += chr
			pos += 1
	elif isCDATA:
		pos += 9
		while pos < lenStr:
			if str[pos:pos+3] == ']]>':
				buf = '<![CDATA[' + buf + ']]>'
				break

			chr = str[pos]

			buf += chr
			pos += 1

	return buf

def matches(patr, str):
	grp = re.match(patr, str)
	return not grp == None

def getTagType(str):
	if str != None:
		if matches('(?s)^\\<\\?.*\\?\\>$', str):
			return 'header'
		elif matches('(?s)^<!--.*-->$', str):
			return 'comment'
		elif matches('(?s)^<!\\[CDATA\\[.*\\]\\]>$', str):
			return 'cdata'
		elif matches('(?s)^</.*>$', str):
			return 'closing'
		elif matches('(?s)^<.*(?<!/)[>]$', str):
			return 'opening'
		elif matches('(?s)^<.*(?<=/)[>]$', str):
			return 'single'
		elif matches('(?s)^[^<].*|.*[^>]$', str):
			return 'content'
	return 'undefined'

def removeLayout(str):
	pos = 0
	prev = ''
	prevType = ''
	buf = []

	while True:
		curStr = getNextToken(str, pos, len(str))
		if curStr == None:
			break

		isLayout = False
		curType = getTagType(curStr)

		if curType == 'content':
			nextPos = pos + len(curStr)
			nextStr = getNextToken(str, nextPos, len(str))

			if not(prevType == 'opening' and getTagType(nextStr) == 'closing'):
				isLayout = True
		
		if not isLayout:
			buf.append(curStr)

		prev = curStr
		prevType = curType
		pos += len(curStr)

		if pos > len(str):
			break

	return ''.join(buf)

def addLayout(str):
	pos = 0
	prev = ''
	prevType = ''
	
	buf = []

	indentLvl = 0
	insideElem = False

	while True:
		curStr = getNextToken(str, pos, len(str))

		if curStr == None:
			break

		curType = getTagType(curStr)

		if curType == 'closing':
			indentLvl -= 1

		if (prevType == 'header' and curType == 'opening' 
		 or prevType == 'closing' and curType == 'opening' 
		 or prevType == 'opening' and curType == 'opening' 
		 or prevType == 'closing' and curType == 'closing'
		 or prevType in ('single', 'comment', 'cdata')
		 or curType in ('single', 'comment', 'cdata')):
			buf.append('\n' + '\t'*indentLvl)

		if curType == 'opening':
			indentLvl += 1	

		buf.append(curStr)
		prev = curStr
		prevType = curType
		pos += len(curStr)

		if pos > len(str):
			break

	return ''.join(buf)