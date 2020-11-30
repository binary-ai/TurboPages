# coding=utf-8

import re
import fnmatch

from urllib.request import urlopen

exclude_pat = {"*/geologiya-uchastka*", "*/calculato*", "*/order*", "*/notes/*", "*.ru", "*.ru/", "*#welcome"}
exceptions = {"*/geologiya-uchastka*"}
ACCORDION_AFTER = 0


def site_map(sub_url, url_range=None):

    xml = urlopen("https://www.mosk-stroy.ru/sitemap.xml").read()

    url_list = re.findall("<loc>(.*)</loc>", xml.decode())
    if url_range:
        include = [sub_url + str(num) for num in range(url_range[0], url_range[1])]
        url_list = [url for url in url_list for inc in include if url.endswith(inc)]
    else:
        url_list = [url for url in url_list if sub_url in url]

    exclude_urls = set()
    for excl in exclude_pat:
        exclude_urls.update(fnmatch.filter(url_list, excl))

    url_list = set(url_list) - exclude_urls
    # for url in url_list:
    #     for excl in exclude_urls:
    #         if url.endswith(excl):
    #             url_list.remove(url)

    # url_list = sorted(url_list)
    return list(url_list)


def parse_page(page_url):

    start_tags = ['serv-content', 'news-list']
    stop_tag = ['</section>', '<!-- Serv-form starts -->']

    text = urlopen(page_url).read().decode()
    h1 = re.findall("<h1.*>(.*)</h1>", text.replace("\n", ""))[0].strip()

    block = ""
    # Delete first H2 tag
    text_block = text[text.find("</h2>")+5:].strip()
    for start_tag in start_tags:
        if start_tag in text_block:
            text_block = text_block[text_block.find(start_tag) + 1:]
            text_block = text_block[text_block.find(">") + 1:].strip()
            block = text_block[:text_block.find(stop_tag[0])]
            text_block = text_block[text_block.find(stop_tag[0])+len(stop_tag[0]):]
        if start_tag in text_block:
            text_block = text_block[text_block.find(start_tag) + 1:]
            text_block = text_block[text_block.find(">") + 1:].strip()
            block = block + text_block[:text_block.find(stop_tag[1])]
    # lookup image by ITS class name!
    image = "".join(re.findall("<img.*src=(.+)alt.*inner-new__img.*>", text.replace("\n", ""))).strip().replace('"', "")
    image = image or "".join(re.findall("<img.*src=(.+)alt.*all-serv__img.*>", text.replace("\n", ""))).strip().replace('"', "")
    wrapped_image = f'''        
        <figure>
          <img src="{image}">
        </figure>
        ''' if image else image

    return h1, block, wrapped_image


def create_turbo_page(url, h1, page_source, image):
    # for i in range(5):
    #     if "<" in h1 and ">" in h1:
    #         h1 = (h1[:h1.find("<")] + h1[h1.find(">") + 1:])
    # h1 = h1.replace("<", "").replace(">", "").replace("\n", " ").strip().strip("/").strip(".")

    page_source = page_source.replace("\n", "").replace("<ul>•", "<br>•")

    # If text is too long - hide the long part under an accordion
    if ACCORDION_AFTER > 0 and len(page_source) > ACCORDION_AFTER * 2:
        page_source = page_source[:page_source[:ACCORDION_AFTER].rfind(" ")] + \
                      ' ..\n          <div data-block="accordion"> <div data-block="item" data-title="Читать далее">' + \
                      page_source[page_source[:ACCORDION_AFTER].rfind(" ")+1:] + "</div></div>"

    content = """

    <!--	%s	-->

    <item turbo="true">
      <title>%s</title>
      <link>%s</link>
      <turbo:content>
        <![CDATA[
          <header><h1>%s</h1>%s</header>
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
        image,
        page_source)
    return content


def create_turbo_pages(few_url):
    turbo_pages = []
    for url in few_url:
        h1, page_source, img = parse_page(url)
        if not page_source:
            raise Exception("NO DATA ON THE PAGE %s" % url)
        else:
            print(h1)
            print(page_source)

        turbo_page = create_turbo_page(url, h1, page_source, img)
        turbo_pages.append(turbo_page)
    return turbo_pages


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

    urls = site_map("/uslugi/")
    filename = "turbo_uslugi_%s.rss"

    for i in range(0, len(urls), 50):
        turbo_pages = create_turbo_pages(urls[i:i+50])

        rss_file_content = wrap_turbo_pages(turbo_pages)
        open(filename % i, "w").writelines(rss_file_content)
