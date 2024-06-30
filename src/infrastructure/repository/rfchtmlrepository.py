
import os
import re
import glob
from ...domain.models.rfc import RfcFile, IRfc
from ...domain.models.html import HtmlFile
from ...domain.repository.irfchtmlrepository import IRfcHtmlRepository


class RfcHtmlFileRepository(IRfcHtmlRepository):

    def findpath(self, rfc: IRfc) -> str:
        return RfcFile.get_filepath_html_rfc(rfc)

    def find(self, rfc: IRfc) -> str:
        filepath = self.findpath(rfc)
        if not os.path.isfile(filepath):
            return None
        obj = RfcFile.read_html_file(filepath)  # HTML入力
        return obj

    def save(self, rfc: IRfc, output_string: object) -> None:
        filepath = self.findpath(rfc)
        RfcFile.write_html_file(filepath, output_string)  # HTML出力

    def delete(self, rfc: IRfc) -> bool:
        filepath = self.findpath(rfc)
        if os.path.isfile(filepath):
            os.remove(filepath)
            return True
        return False

    def findall(self) -> list[HtmlFile]:
        """RFC全件取得"""
        files = []
        for filepath in glob.glob(RfcFile.GLOB_HTML_FILE):
            html = RfcFile.read_html_file(filepath)
            m = re.search(r'<title>([^<]*)</title>', html)
            if not m:
                print("[-] not found title: %s" % filepath)
                continue
            title = m[1].replace('日本語訳', '').strip()
            filename = os.path.basename(filepath)
            if m := re.match(r'rfc(\d+).html', filename):
                filenum = int(m[1])
                if filenum < 2220:  # RFC 2220 以降を対象とする
                    continue
                files.append(HtmlFile(filenum, filename, title))

        # RFC番号順（降順）でソート
        files.sort(reverse=True, key=lambda x: x.get_id())
        return files

    def findalldraft(self) -> list[HtmlFile]:
        """Draft版RFC全件取得"""
        files = []
        for filepath in glob.glob(RfcFile.GLOB_HTML_DRAFT_FILE):
            html = RfcFile.read_html_file(filepath)
            m = re.search(r'<title>([^<]*)</title>', html)
            if not m:
                print("[-] not found title: %s" % filepath)
                continue
            title = m[1].replace('日本語訳', '').strip()

            rfcfile = os.path.basename(filepath)
            if m := re.match(r'draft-[^-]+-(?P<draftname>.*).html', rfcfile):
                filenum = m['draftname']
                files.append(HtmlFile(filenum, rfcfile, title))

        # RFCドラフト名でソート
        files.sort(key=lambda x: x.get_id())
        return files