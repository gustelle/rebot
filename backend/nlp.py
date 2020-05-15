# -*- coding: utf-8 -*-

import re


class FeaturesExtractor(object):
    """Simple language processing which extracts basic keywords from texts
    """

    def __init__(self, property_ad):
        """"""
        self.document = property_ad


    def extract(self):
        """"""
        features = []

        m = re.search(r'.*(?P<chambres>\d{1,}\s{1,}\bchambre(s)?\b).*', self.document, re.IGNORECASE)
        if m:
            features.append(m.group('chambres'))

        m = re.search(r'.*(?P<jardin>\bjardin\b).*', self.document, re.IGNORECASE)
        if m:
            features.append(m.group('jardin'))

        m = re.search(r'.*(?P<garage>\bgarage\b).*', self.document, re.IGNORECASE)
        if m:
            features.append(m.group('garage'))

        return features
