
import re
import textwrap
import datetime
from pprint import pprint
import xml2rfc  # pip install xml2rfc
from xml2rfc.writers.base import default_options
from xml2rfc.writers.text import TextWriter
from ...domain.services.rfcutils import RfcUtils
from ...domain.valueobject.rfc.contents.content import Content


def _get_parent(elem):
    """XMLツリーの現在の要素から見た親要素を取得する"""
    return elem.find('..')

def _has_ancestor(elem, tagname: str) -> bool:
    """XMLツリーの現在の要素から見た先祖の要素に指定したタグ名が含まれるときTrueを返す"""
    current = elem
    while True:
        parent = _get_parent(current)
        if parent is None:
            return False
        if parent.tag == tagname:
            return True
        current = parent

def _get_tag_path(elem) -> str:
    """XMLツリーのルートから現在の要素までのタグ一覧を表示する"""
    return '/' + '/'.join([a.tag for a in elem.iterancestors()][::-1]) + '/' + elem.tag


# xml2rfc
# https://github.com/ietf-tools/xml2rfc/blob/main/xml2rfc/writers/text.py

# xml2rfcのデフォルト値設定
dt_now = datetime.datetime.now()
default_options.date = dt_now
default_options.pagination = False
default_options.rfc = True

# nameタグ
#   section > name
#   references > name
_textwriter_render_name = TextWriter.render_name
def _new_textwriter_render_name(self, e, width, **kwargs):
    res = _textwriter_render_name(self, e, width, **kwargs)
    parent_e = _get_parent(e)
    if parent_e.tag in ('section'):
        # 親要素がセクション(sectionタグ)のとき
        pre_text = ''
        pn = parent_e.get('pn', 'unknown-unknown')
        if parent_e.get('numbered') == 'true':
            _, num, _ = self.split_pn(pn)
            pre_text = num.title() + '.'
            if self.is_appendix(pn) and self.is_top_level_section(num):
                pre_text = 'Appendix %s' % pre_text
        text = f'{pre_text} {res}'.strip()
        self._contents.append(Content(text, section_title=True, tag=_get_tag_path(e)))
    elif parent_e.tag in ('references'):
        # 親要素が参考資料(referencesタグ)のとき
        pn = parent_e.get('pn')
        pre_text = pn.split('-',1)[1].replace('-', ' ').title() + '.'
        text = f'{pre_text}  {res}'
        self._contents.append(Content(text, section_title=True, tag=_get_tag_path(e)))
    return res
TextWriter.render_name = _new_textwriter_render_name

# tタグ
#   ul > li > t
#   ol > li > t
#   aside > t
_textwriter_render_t = TextWriter.render_t
def _new_textwriter_render_t(self, e, width, **kwargs):
    res = _textwriter_render_t(self, e, width, **kwargs)
    # 箇条書きのとき、最も近い親要素が ul か ol かを判定する
    ancestor_tag = None
    for parent in e.iterancestors():
        if parent.tag in ('ul', 'ol'):
            ancestor_tag = parent.tag
            break
        elif parent.tag in ('dl'):
            ancestor_tag = parent.tag
            break
    if _has_ancestor(e, tagname='toc'):
        # 親要素が目次(toc) のときは何もしない
        pass
    elif _has_ancestor(e, tagname='table'):
        # 親要素が表(table) のときは何もしない
        pass
    elif ancestor_tag == 'ul':
        # 親要素が箇条書きリスト(ul > li)のとき
        ancestor_ols = [ a for a in e.iterancestors('ol') ]
        ancestor_uls = [ a for a in e.iterancestors('ul') ]
        ancestor_ul = ancestor_uls[0]
        indent = (sum([a._padding * 2 for a in ancestor_ols if hasattr(a, '_padding')]) + \
                sum([a._padding * 2 for a in ancestor_uls if hasattr(a, '_padding')]))
        pre_text = ancestor_ul._initial_text(e, ancestor_ul)
        text = '\n'.join([r.text for r in res])
        out_text = f'{pre_text}{text}'
        # li直下に複数のtタグが存在するときの対応
        if _get_parent(e).tag == 'li' and len(re.findall(r'\.1$', e.get('pn', ''))) == 0:
            out_text = f'{text}'
            indent += 4
        self._contents.append(Content(out_text, indent=indent, tag=_get_tag_path(e)))
    elif ancestor_tag == 'ol':
        # 親要素が順序リスト(ol > li)のとき
        ancestor_ols = [ a for a in e.iterancestors('ol') ]
        ancestor_uls = [ a for a in e.iterancestors('ul') ]
        # 自分自身がliのとき
        pre_text = e.get('derivedCounter', None)
        if not pre_text:
            # 自分自身がtで親がliのとき
            ancestor_lis = [ a for a in e.iterancestors('li') ]
            if len(ancestor_lis) > 0:
                pre_text = ancestor_lis[0].get('derivedCounter', '1.')
            else:
                pre_text = '1.'
        indent = (sum([a._padding * 2 for a in ancestor_ols if hasattr(a, '_padding')]) + \
                  sum([a._padding * 2 for a in ancestor_uls if hasattr(a, '_padding')]))
        text = '\n'.join([r.text for r in res])
        out_text = f'{pre_text} {text}'
        # li直下に複数のtタグが存在するときの対応
        if _get_parent(e).tag == 'li' and len(re.findall(r'\.1$', e.get('pn', ''))) == 0:
            out_text = f'{text}'
            indent += 4
        self._contents.append(Content(out_text, indent=indent, tag=_get_tag_path(e)))
    elif ancestor_tag == 'dl':
        # 親要素が定義(dl)のとき
        text = '\n'.join([r.text for r in res]).rstrip('\n').lstrip()
        ancestors = [ a for a in e.iterancestors() if a.tag in ('ul', 'ol', 'dl') ]
        indent = len(ancestors) * 3 + 9
        self._contents.append(Content(text, indent=indent, tag=_get_tag_path(e)))
    elif e.attrib.get('pn'):
        # tタグ
        text = '\n'.join([r.text for r in res])
        joiners = kwargs['joiners']
        j = joiners[e.tag] if e.tag in joiners else joiners[None]
        indent = j.indent
        if _get_parent(e).tag == 'aside':
            # 引用のときはインデント追加
            indent += 12
        self._contents.append(Content(text, indent=indent, tag=_get_tag_path(e)))
    return res
TextWriter.render_t = _new_textwriter_render_t

# dtタグ
#   dl > dt
_textwriter_render_dt = TextWriter.render_dt
def _new_textwriter_render_dt(self, e, width, **kwargs):
    res = _textwriter_render_dt(self, e, width, **kwargs)
    if e.attrib.get('pn'):
        text = '\n'.join([r.text for r in res]).rstrip('\n')
        ancestors = [ a for a in e.iterancestors() if a.tag in ('ol', 'ul', 'dl') ]
        ancestors_count = len(ancestors)
        indent = ancestors_count * 3
        self._contents.append(Content(text, indent=indent, tag=_get_tag_path(e)))
    return res
TextWriter.render_dt = _new_textwriter_render_dt

# artworkタグ
#   section > artwork
textwriter_render_artwork = TextWriter.render_artwork
def new_textwriter_render_artwork(self, e, width, **kwargs):
    res = textwriter_render_artwork(self, e, width, **kwargs)
    if not _has_ancestor(e, tagname='figure'):
        joiners = kwargs['joiners']
        j = joiners[e.tag] if e.tag in joiners else joiners[None]
        base_indent = j.indent
        artwork = '\n'.join([r.text for r in res]).rstrip('\n')
        artwork = artwork.strip('\n')
        indent = base_indent + RfcUtils.get_indent_multiline(artwork)
        text = textwrap.dedent(artwork)
        self._contents.append(Content(text, indent=indent, raw=True, tag=_get_tag_path(e)))
    return res
TextWriter.render_artwork = new_textwriter_render_artwork

# figureタグ
#   section > figure > artwork
_textwriter_render_figure = TextWriter.render_figure
def _new_textwriter_render_figure(self, e, width, **kwargs):
    res = _textwriter_render_figure(self, e, width, **kwargs)
    if e.attrib.get('pn'):
        text = '\n'.join([r.text for r in res]).rstrip('\n')
        matchobj = re.finditer(re.compile(r'^\s*Figure \d+:', re.MULTILINE), text)
        mlist = [x for x in matchobj]
        if len(mlist) > 0:
            m = mlist[-1]
            fig = text[0:m.start()]
            figname = text[m.start():]
            # 基本のインデント
            joiners = kwargs['joiners']
            j = joiners[e.tag] if e.tag in joiners else joiners[None]
            base_indent = j.indent
            # 図
            fig = fig.strip('\n')
            indent = base_indent + RfcUtils.get_indent_multiline(fig)
            text = textwrap.dedent(fig)
            self._contents.append(Content(text, indent=indent, raw=True, tag=_get_tag_path(e)))
            # 図の表題
            figname = figname.strip('\n')
            indent = base_indent + RfcUtils.get_indent_multiline(figname)
            text = textwrap.dedent(figname)
            self._contents.append(Content(text, indent=indent, tag=_get_tag_path(e)))
        else:
            fig = text.strip('\n')
            indent = RfcUtils.get_indent_multiline(fig)
            text = textwrap.dedent(fig)
            self._contents.append(Content(text, indent=indent, raw=True, tag=_get_tag_path(e)))
    return res
TextWriter.render_figure = _new_textwriter_render_figure

# tableタグ
#   table > tr > td
_textwriter_render_table = TextWriter.render_table
def _new_textwriter_render_table(self, e, width, **kwargs):
    res = _textwriter_render_table(self, e, width, **kwargs)
    if e.attrib.get('pn'):
        text = '\n'.join([r.text for r in res])
        matchobj = re.finditer(re.compile(r'^\s*Table \d+:', re.MULTILINE), text)
        mlist = [x for x in matchobj]
        if len(mlist) > 0:
            m = mlist[-1]
            table = text[0:m.start()]
            tablename = text[m.start():]
            # 表
            table = table.strip('\n')
            indent = RfcUtils.get_indent_multiline(table) + 3  # インデント追加
            text = textwrap.dedent(table)
            self._contents.append(Content(text, indent=indent, raw=True, tag=_get_tag_path(e)))
            # 表の表題
            tablename = tablename.strip('\n')
            indent = RfcUtils.get_indent_multiline(tablename) + 3  # インデント追加
            text = textwrap.dedent(tablename)
            self._contents.append(Content(text, indent=indent, tag=_get_tag_path(e)))
        else:
            indent = RfcUtils.get_indent_multiline(text)
            self._contents.append(Content(text, indent=indent, raw=True, tag=_get_tag_path(e)))
    return res
TextWriter.render_table = _new_textwriter_render_table

# first_page_top (frontタグ)  -- RFCのヘッダー部分
#   rfc > front
_textwriter_render_first_page_top = TextWriter.render_first_page_top
def _new_textwriter_render_first_page_top(self, e, width, **kwargs):
    res = _textwriter_render_first_page_top(self, e, width, **kwargs)
    text = res
    matchobj = re.finditer(re.compile(r'\n\n', re.MULTILINE), text)
    mlist = [x for x in matchobj]
    if len(mlist) > 0:
        m = mlist[-1]
        front = text[0:m.start()]
        fronttitle = text[m.start():]
        # ヘッダー
        indent = RfcUtils.get_indent(front)
        self._contents.append(Content(front, indent=indent, raw=True, tag=_get_tag_path(e)))
        # タイトル
        indent = RfcUtils.get_indent(fronttitle.lstrip('\n'))
        fronttitle = textwrap.dedent(fronttitle.lstrip('\n'))
        self._contents.append(Content(fronttitle, indent=indent, title=True, section_title=True, tag=_get_tag_path(e)))
    return res
TextWriter.render_first_page_top = _new_textwriter_render_first_page_top

# abstractタグ
#   rfc > front > abstract
_textwriter_render_abstract = TextWriter.render_abstract
def _new_textwriter_render_abstract(self, e, width, **kwargs):
    text = 'Abstract'
    self._contents.append(Content(text, indent=0, section_title=True, tag=_get_tag_path(e)))
    res = _textwriter_render_abstract(self, e, width, **kwargs)
    return res
TextWriter.render_abstract = _new_textwriter_render_abstract

# tocタグ
#   rfc > front > toc
_textwriter_render_toc = TextWriter.render_toc
def _new_textwriter_render_toc(self, e, width, **kwargs):
    res = _textwriter_render_toc(self, e, width, **kwargs)
    if len(res) > 0 and re.match(r'Table[\s]of[\s]Contents', res[0].text):
        res = res[1:]  # 最初の行 ("Table of Contents") は削除
        toc = '\n'.join([r.text for r in res]).rstrip('\n')
        joiners = kwargs['joiners']
        j = joiners[e.tag] if e.tag in joiners else joiners[None]
        base_indent = j.indent
        toc = toc.strip('\n')
        indent = base_indent + RfcUtils.get_indent_multiline(toc)
        text = textwrap.dedent(toc)
        self._contents.append(Content(text, indent=indent, raw=True, toc=True, tag=_get_tag_path(e)))
    return res
TextWriter.render_toc = _new_textwriter_render_toc

# referencegroupタグ
#   rfc > back > references > referencegroup > reference
_textwriter_render_referencegroup = TextWriter.render_referencegroup
def _new_textwriter_render_referencegroup(self, e, width, **kwargs):
    res = _textwriter_render_referencegroup(self, e, width, **kwargs)
    if e.get('anchor'):
        text = '\n'.join([r.text for r in res]).rstrip('\n')
        indent = 3
        self._contents.append(Content(text, indent=indent, raw=True, tag=_get_tag_path(e)))
    return res
TextWriter.render_referencegroup = _new_textwriter_render_referencegroup

# referenceタグ
#   rfc > back > references > reference
_textwriter_render_reference = TextWriter.render_reference
def _new_textwriter_render_reference(self, e, width, **kwargs):
    res = _textwriter_render_reference(self, e, width, **kwargs)
    if e.get('anchor') and not _has_ancestor(e, tagname='referencegroup'):
        text = '\n'.join([r.text for r in res]).rstrip('\n')
        joiners = kwargs['joiners']
        j = joiners[e.tag] if e.tag in joiners else joiners[None]
        indent = j.indent
        self._contents.append(Content(text, indent=indent, raw=True, tag=_get_tag_path(e)))
    return res
TextWriter.render_reference = _new_textwriter_render_reference

# authorタグ
#   section > author
_textwriter_render_author = TextWriter.render_author
def _new_textwriter_render_author(self, e, width, **kwargs):
    res = _textwriter_render_author(self, e, width, **kwargs)
    if _get_parent(e).tag == 'section':
        text = '\n'.join([r.text for r in res]).rstrip('\n')
        joiners = kwargs['joiners']
        j = joiners[e.tag] if e.tag in joiners else joiners[None]
        indent = j.indent
        self._contents.append(Content(text, indent=indent, raw=True, tag=_get_tag_path(e)))
    return res
TextWriter.render_author = _new_textwriter_render_author


def generate_text_writer(xml: bytes):
    """xml2rfcのTextWriterのインスタンスを作成する"""
    options_for_xmlrfcparser = dict()
    parser = xml2rfc.XmlRfcParser(None, quiet=True, options=default_options, **options_for_xmlrfcparser)
    parser.text = xml
    xmlrfc = parser.parse()
    text_writer = xml2rfc.TextWriter(xmlrfc, quiet=True)
    # 解析後はグローバル変数contentsに段落ごとの情報が格納される
    setattr(text_writer, '_contents', [])
    return text_writer
