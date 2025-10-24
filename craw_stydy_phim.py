from bs4 import BeautifulSoup

with open("data.html", "r", encoding="utf-8") as fp:
    soup = BeautifulSoup(fp, 'html.parser')
    soup.select('.show-sub span')
    content = []
    # print(soup.select('.show-sub span'))
    for item in soup.select('.show-sub > span'):
        vi = item.select_one('small.js-textVi').text.strip()
        content.append(vi)
        en = item.select_one('span.js-textEn').text.strip()
        content.append(en)
        print(item.select_one('span.js-textEn').text.strip())
        print(item.select_one('small.js-textVi').text.strip())
        print('---')
    with open("data.txt", "w", encoding="utf-8") as fp:
        fp.write('\n'.join(content))
