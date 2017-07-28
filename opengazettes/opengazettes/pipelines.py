# -*- coding: utf-8 -*-

import os.path
import logging
from scrapy.http import Request, FormRequest
from scrapy.utils.request import referer_str
from scrapy.pipelines.files import FilesPipeline
from scrapy.pipelines.files import FileException

try:
    from cStringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO

logger = logging.getLogger(__name__)


class OpengazettesFilesPipeline(FilesPipeline):

    def media_downloaded(self, response, request, info):
        referer = referer_str(request)

        if response.status != 200:
            logger.warning(
                'File (code: %(status)s): Error downloading file from '
                '%(request)s referred in <%(referer)s>',
                {'status': response.status,
                 'request': request, 'referer': referer},
                extra={'spider': info.spider}
            )
            raise FileException('download-error')

        buf = BytesIO(response.body)
        # Tag files that have errors in them
        has_error = True if 'A PHP Error was encountered'\
            in buf.read() else False

        if not response.body:
            logger.warning(
                'File (empty-content): Empty file from %(request)s referred '
                'in <%(referer)s>: no-content',
                {'request': request, 'referer': referer},
                extra={'spider': info.spider}
            )
            raise FileException('empty-content')

        status = 'cached' if 'cached' in response.flags else 'downloaded'
        logger.debug(
            'File (%(status)s): Downloaded file from %(request)s referred in '
            '<%(referer)s>',
            {'status': status, 'request': request, 'referer': referer},
            extra={'spider': info.spider}
        )
        self.inc_stats(info.spider, status)

        try:
            path = self.file_path(request, response=response, info=info)
            checksum = self.file_downloaded(response, request, info)
        except FileException as exc:
            logger.warning(
                'File (error): Error processing file from %(request)s '
                'referred in <%(referer)s>: %(errormsg)s',
                {'request': request, 'referer': referer, 'errormsg': str(exc)},
                extra={'spider': info.spider}, exc_info=True
            )
            raise
        except Exception as exc:
            logger.error(
                'File (unknown-error): Error processing file from %(request)s '
                'referred in <%(referer)s>',
                {'request': request, 'referer': referer},
                exc_info=True, extra={'spider': info.spider}
            )
            raise FileException(str(exc))

        return {'url': request.url, 'path': path, 'checksum': checksum,
                'has_error': has_error}

    def get_media_requests(self, item, info):

        # return [Request(x, meta={'filename': item["filename"],
        #                          'publication_date': item["publication_date"], ''}, method='POST', )
        #         for x in item.get(self.files_urls_field, [])]
        get_cookies = []
        for i, x in enumerate(item.get(self.files_urls_field, [])):
            one_response = Request(x, meta={
                                   'filename': item["filename"], 'publication_date': item["publication_date"], 'cookiejar': i})
            get_cookies.append(one_response)

        final_response = []
        for response in get_cookies:
            form_stuff = response.css('form input[type="hidden"]').extract()
            download_id = form_stuff[1].split()
            download_id = download_id[len(
                download_id) - 1].split('"')[1].split('"')
            file_key = form_stuff[2].split()[2].split('"')[1]
            formdata = {"submit": "Download", "license_agree": "1",
                        "download": download_id, file_key: "1"}

            headers = {"Host": "www.utumishi.go.tz",
                       "Connection": "keep-alive",
                       "Content-Length": "78",
                       "Cache-Control": "max-age=0",
                       "Origin": "http://www.utumishi.go.tz",
                       "Upgrade-Insecure-Requests": "1",
                       "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36",
                       "Content-Type": "application/x-www-form-urlencoded",
                       "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                       "Referer": "http://www.utumishi.go.tz/utumishiweb/index.php?option=com_phocadownload&view=file&id=88:toleo-na-16-la-tarehe-20-aprili-2012&Itemid=179&lang=en",
                       "Accept-Encoding": "gzip, deflate",
                       "Accept-Language": "en-US,en;q=0.8"}

            each_file = FormRequest(response.url, meta={
                'filename': item["filename"], 'publication_date': item["publication_date"], 'cookiejar': response.meta['cookiejar']}, headers=headers, formdata=formdata)
            final_response.append(each_file)
        
        return final_response

    def file_path(self, request, response=None, info=None):
        # start of deprecation warning block (can be removed in the future)
        def _warn():
            from scrapy.exceptions import ScrapyDeprecationWarning
            import warnings
            warnings.warn('FilesPipeline.file_key(url) method is deprecated,\
            please use file_path(request, response=None, info=None) instead',
                          category=ScrapyDeprecationWarning, stacklevel=1)

        # check if called from file_key with url as first argument
        if not isinstance(request, Request):
            _warn()
            url = request
        else:
            url = request.url

        # detect if file_key() method has been overridden
        if not hasattr(self.file_key, '_base'):
            _warn()
            return self.file_key(url)
        # end of deprecation warning block

        # Now using file name passed in the meta data
        filename = request.meta['filename']
        media_ext = os.path.splitext(url)[1]
        return '%s/%s/%s%s' % \
            (request.meta['publication_date'].strftime("%Y"),
                request.meta['publication_date'].strftime("%m"),
                filename, media_ext)
