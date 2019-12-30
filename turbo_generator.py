# coding=utf-8

import re

from selenium.webdriver import Chrome

driver = None
exclude_urls = ["new=1", "new=45", "new=40", "new=69"]


def site_map(sub_url, url_range=None):
    driver.get("https://www.mosk-stroy.ru/sitemap.xml")
    text = driver.page_source
    url_list = re.findall("<loc>(.*)</loc>", text)
    if url_range:
        include = [sub_url + str(num) for num in range(url_range[0], url_range[1])]
        url_list = [url for url in url_list for inc in include if url.endswith(inc)]
    else:
        url_list = [url for url in url_list if url.endswith(sub_url)]

    for url in url_list:
        for excl in exclude_urls:
            if url.endswith(excl):
                url_list.remove(url)

    url_list = sorted(url_list)
    return url_list


def parse_page(page_url):
    start_title_tag = '<h1>'
    stop_title_tag = '</h1>'
    stop_tag = '<div id="mc-container">'
    stop_tag_2 = '<tr class="footer">'
    driver.get(page_url)
    text = driver.page_source
    h1 = text[text.find(start_title_tag)+len(start_title_tag):text.find(stop_title_tag)]
    if stop_tag in text:
        text = text[text.find(stop_title_tag)+len(stop_title_tag):text.find(stop_tag)]
    elif stop_tag_2 in text:
        text = text[text.find(stop_title_tag)+len(stop_title_tag):text.find(stop_tag_2)]
    # print(text)
    return h1, text


def create_turbo_page(url, h1, page_source):
    for i in range(5):
        if "<" in h1 and ">" in h1:
            h1 = (h1[:h1.find("<")] + h1[h1.find(">") + 1:])
    h1 = h1.replace("<", "").replace(">", "").replace("\n", " ").strip().strip("/").strip(".")

    page_source = page_source.replace("\n", "").replace("<ul>•", "<br>•")

    # If text is too long - hide the long part under an accordion
    if len(page_source) > 4000:
        cut_from = 2000
        page_source = page_source[:page_source[:cut_from].rfind(" ")] + \
                      ' ..\n          <div data-block="accordion"> <div data-block="item" data-title="Читать далее">' + \
                      page_source[page_source[:cut_from].rfind(" ")+1:] + "</div></div>"

    content = """

    <!--	%s	-->

    <item turbo="true">
      <title>%s</title>
      <link>%s</link>
      <turbo:content>
        <![CDATA[
          <header><h1>%s</h1></header>
          %s
          <button formaction="tel:+7(495)724-20-30" data-background-color="#5B97B0" data-color="white" data-primary="true">Позвонить</button>
        ]]>
      </turbo:content>
    </item>
    """ % (
        url[url[:-2].rfind("/"):],
        h1,
        url,
        h1,
        page_source)
    return content


def wrap_turbo_pages(pages):
    content = """
<rss xmlns:yandex="http://news.yandex.ru" xmlns:turbo="http://turbo.yandex.ru" version="2.0">
<channel>
    <title>Инженерные изыскания</title>
    <link>https://www.mosk-stroy.ru/</link>
    <description>Инженерные изыскания под строительства</description>
    
    %s

    </channel>
</rss>
    """ % "".join(pages)
    return content


if __name__ == '__main__':
    driver = Chrome()
    urls = site_map("page=", (0, 10))
    filename = "turbo_html.rss"

    turbo_pages = []
    for url in urls:
        h1, page_source = parse_page(url)
        turbo_page = create_turbo_page(url, h1, page_source)
        turbo_pages.append(turbo_page)

    driver.quit()

    rss_file_content = wrap_turbo_pages(turbo_pages)
    open(filename, "w").writelines(rss_file_content)
