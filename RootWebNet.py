
import urllib
import re
import urllib.parse
import urllib.request
from bs4 import BeautifulSoup
import urllib.error
import os


alldatalinks = set()
dataname = set()
dataimg = set()
datalink = set()
datatime = set()
dataURLLinks = set()
dataURLSeedLinks = set()

# 以下三个页面规则不同，暂时规避，避免爬虫死机
alldatalinks.add("/Html/63/")
alldatalinks.add("/Html/84/")
alldatalinks.add("/Html/92/")
alldatalinks.add("/Html/86/")
fdataw = open(r'Data\data.txt', 'w')

def gethtml(url, num_retries=5):

    # 设置编码
    # sys.setdefaultencoding('utf-8')
    # 获得系统编码
    # type = sys.getfilesystemencoding()

    header = {'User-Agent': r'Mozilla/5.0 (Windows NT 6.1; WOW64)AppleWebKit/537.36 (KHTML, like Gecko)'
                r'Chrome/45.0.2454.85 Safari/537.36 115Browser/6.0.3'}
    req = urllib.request.Request(url, headers=header)
    try:
        # 间隔6秒访问
        # time.sleep(6)
        html = urllib.request.urlopen(req).read()
        # 将网页以utf-8 格式解析然后转换为系统默认格式
        # html = html.decode('utf-8')
    except urllib.error.HTTPError as e:
        # if hasattr(e, 'reason'):
        print('Download error:', e.reason)
        if num_retries > 0:
            if hasattr(e, 'code') and 500 <= e.code < 600:
                print(e.code)
                # recursively retry 5xx HTTP errors
                return gethtml(url, num_retries-1)
            else:
                html = None
    return html


def getInternalLinks(bsObj):
    """ 获取页面所有内链的列表"""
    print("in")
    internalLinks = []
    TagDiv = bsObj.find_all('div', class_='wrap')
    print(len(TagDiv))
    for x in range(0, len(TagDiv)-3):
        print(str(x))
        for link in TagDiv[x].findAll("a", href=re.compile("^(/Html"+")")):
            if link.attrs['href'] is not None:
                if link.attrs['href'] not in internalLinks:
                    print(link.attrs['href'])
                    internalLinks.append(link.attrs['href'])
    return internalLinks


def getExternalLinks(bsObj, excludeUrl):
    """  获取页面所有外链的列表"""

    externalLinks = []
    # 找出所有以"http"或"www"开头且不包含当前URL的链接
    for link in bsObj.findAll("a", href=re.compile("^(http|www)((?!"+excludeUrl+").)*$")):
        if link.attrs['href'] is not None:
            if link.attrs['href'] not in externalLinks:
                externalLinks.append(link.attrs['href'])
    return externalLinks


def splitAddress(address):
    addressParts = address.replace("http://", "").split("/")
    return addressParts

def TestURL(turl):
    thtml = gethtml(turl)
    if thtml is None:
        return 0
    return 1


def getAllLinks(startURL):

    print("start")
    allInterLinks = set()
    allExtLinks = set()
    global alldatalinks
    global fdataw
    """
    html = gethtml(startURL)
    bsObj = BeautifulSoup(html, 'lxml')
    internalLinks = getInternalLinks(bsObj)
    externalLinks = getExternalLinks(bsObj, splitAddress(startURL)[0])
    for link in externalLinks:
        if link not in allExtLinks:
            print("find : "+link)
            allExtLinks.add(link)"""
    fw = open(r'URLList.txt', 'r')
    Links = set()
    lines = fw.readlines()
    for line in lines:
        strurl = line.split("\n")[0]
        Links.add(strurl)
    fw.close()
    for link in Links:
        print("into a theme: ")
        print(link)
        fdataw.write("Theme : " + link + "\n")
        if link not in allInterLinks:
            allInterLinks.add(link)
            newThemeURL = urllib.parse.urljoin(startURL, link)
            if TestURL(newThemeURL):
                print("     "+link + "is OK")
                analyzeInterLink(newThemeURL)
    fdataw.close()
    furl = open(r'DataURL.txt', 'w')
    for str in alldatalinks:
        furl.write(str + "\n")
    furl.close()


def analyzeInterLink(interURL):

    end = 1
    global alldatalinks
    # tem = splitAddress(interURL)
    interhtml = gethtml(interURL)
    number = 1
    while end == 1:
        number += 1
        print("into: "+interURL + " get datahtml link")
        bsObj = BeautifulSoup(interhtml, 'lxml')
        links = bsObj.find('div', class_="box movie_list").find_all('li')
        for li in links:
            link = li.a.attrs['href']
            if link not in alldatalinks:
                alldatalinks.add(link)
                newurl = urllib.parse.urljoin(interURL, link)
                # 测试该页第一个资源链接是否有效，无效则后期该页起的的所有页，并进入一个一主题
                if TestURL(newurl):
                    analyzeDataHtml(newurl)
                else:
                    return 
        nextURL = urllib.parse.urljoin(interURL, "index-" + str(number) + ".html")
        interhtml = gethtml(nextURL)
        interURL = nextURL
        print("得到新值：" + nextURL)
        print("一页结束 : "+str(end))
        # 到达尾页 即index-n.html not found
        if interhtml is None:
            print("  them :" + interURL.split('/')[2] + ' index-' + str(number) + "Not Found " )
            return


def analyzeDataHtml(dataURL):
    """ 从资源HTML中提取资源名称，发布时间，图形，磁链接 """
    global dataimg
    global datalink
    global dataname
    global datatime
    print("     try into: " + dataURL + " get xunlei link")
    datahtml = gethtml(dataURL)
    bsObj = BeautifulSoup(datahtml, 'lxml')
    tag = bsObj.find('div', class_='movie_info')
    temstr = tag.h1.string
    dataname.add(temstr)
    tag1 = bsObj.find('div', class_='movie_info').find_all('dd')
    ttime = tag1[4].contents[0]
    datatime.add(tag1[4].contents[0])
    # 获取磁链接
    tag2 = bsObj.find_all('div', class_='film_bar clearfix')
    # 有在线播放和迅雷链接 连个<a>链接，隶属于<div class = film_bar clearfix>
    # 因此 len(tag2)=2或1
    # 有些资源没有磁链接，只有在线播放
    # 总是获取最后一个<div class => ，可以保证有迅雷时获取迅雷无迅雷时获取在线播放
    datalink = tag2[len(tag2)-1].a.attrs['href']
    tag3 = bsObj.find('div', class_='movie_info').find('dt')
    img = tag3.img.attrs['src']
    dataimg.add(tag3.img.attrs['src'])
    WriteData(temstr, ttime, datalink, img)


def WriteData(n, t, l, i):

    global dataimg
    global datalink
    global dataname
    global datatime
    global fdataw

    print("write " + l)
    str1 = "name : " + n + "\n"
    str2 = "time : " + t + "\n"
    str3 = "link : " + l + "\n"
    str4 = "img : " + i + "\n"
    """
    str1 = str1.encode('gbk')
    str3 = str3.encode('gbk')
    str2 = str2.encode('gbk')
    str4 = str4.encode('gbk')"""
    li = [str1, str2, str3, str4]
    try:
        fdataw.writelines(li)
    except:
        print('write  error')


if __name__ == "__main__":
    getAllLinks("https://www.482j.com")


