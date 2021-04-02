# -*- coding: latin-1 -*-
#
# Raspberry Pi Radio Character translation codes
# HTML entities used by the RSS class (rss_class.py)
#
# $Id: HTMLcodes.py,v 1.2 2020/10/11 06:46:17 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#            The authors shall not be liable for any loss or damage however caused.
#
# Useful Links on character encodings
#       http://www.zytrax.com/tech/web/entities.html

rss_amp_codes = {
        '&amp;raquo;' : ">>",   # Right double angle (Russian) preceded by &amp;
        '&amp;laquo;' : ">>",   # Left double angle (Russian) preceded by &amp;
}

html_entities = {
    # HTML Entities. See https://dev.w3.org/html5/html-author/charref
    '&raquo;' : ">>",       # Right double angle (Russian)
    '&laquo;' : ">>",       # Left double angle (Russian)
    '&amp;' : " ",          # Ampersand
    '&apos;' : "'",         # Apostrophe
    '&nbsp;' : " ",         # Space
    '&quot;' : '"',         # Quotation mark
    '&lt;' : "<",           # Less than
    '&gt;' : ">",           # Greater than
    '&pound;' : "#",        # Pound
    '&cent;' : "c",         # Cent
    '&copy;' : "(C)",       # Copyright
    '&reg;' : "(R)",        # Registered

    # Special characters
    '\t' : " ",     # Tabs
    '\n' : " ",     # Newlines
}

# Tags to strip out but leave text
tags = ('<h1>', '</h1>',
        '<h2>', '</h2>',
        '<h3>', '</h3>',
        '<h4>', '</h4>',
        '<h5>', '</h5>',
        '<em>', '</em>',
        '<div>', '</div>',
        '<sub>', '</sub>',
        '<sup>', '</sup>',
        '<del>', '</del>',
        '<ins>', '</ins>',
        '<mark>', '</mark>',
        '<b>', '</b>',
        '<u>', '</u>',
        '<i>', '</i>',
        '<p>', '</p>', '<p/>',
        '<li>', '</li>',
        '<br>', '</br>','<br/>',
        '<strong>', '</strong>',
        '<title>', '</title>',
        '<description>', '</description>',
        )

# Delete both tags and all content between them
# These must be specified in opening and closing pair
deletion_tags = [
        '<iframe ','</iframe>',
        '<div ','</div>',
        '<dl ','</dl>',
        '<dd ','</dd>',
        '<a ','</a>',
        '<a ','>',
        '<p ','>',
    ]

# End of tags
