import re
import os.path
import codecs
from urlparse import urlparse

# domain is in position 2
URL_PATTERN=re.compile(r"([^:/@]+://)?([^:/@]+:[^:/@]+@)?([^:/@]+)(:\d+)?(/(.*))?$")
TLD_FILE_PATH =os.path.abspath(os.path.join(
                    os.path.dirname(__file__),
                'data/tld_names'))
TLDS = []



def get_domain(url):
    if not TLDS:
        # cache tlds, ignore comments and empty lines:
        with codecs.open(TLD_FILE_PATH, 'r', 'utf-8') as tldFile:
            TLDS.extend(line.strip() for line in tldFile if line[0] not in u"/\n")

    parsed = urlparse(url)
    if not parsed.hostname:
        parsed = urlparse('http://%s' % url)
    urlElements = parsed.hostname.split('.')

    for i in range(-len(urlElements),0):
        lastIElements = urlElements[i:]
        #    i=-3: ["abcde","co","uk"]
        #    i=-2: ["co","uk"]
        #    i=-1: ["uk"] etc

        candidate = ".".join(lastIElements) # abcde.co.uk, co.uk, uk
        wildcardCandidate = ".".join(["*"]+lastIElements[1:]) # *.co.uk, *.uk, *
        exceptionCandidate = "!"+candidate

        # match tlds:
        if (exceptionCandidate in TLDS):
            return ".".join(urlElements[i:])
        if (candidate in TLDS or wildcardCandidate in TLDS):
            return ".".join(urlElements[i-1:])
            # returns "abcde.co.uk"

    raise ValueError("Domain not in global list of TLDs, %s" % (url, ) )


def get_tld(url):
    return '.'.join(get_domain(url).split('.')[1:])


if __name__ == '__main__':
    assert 'domain.co.uk' == get_domain("http://subdomain.domain.co.uk/goo?a=2")
