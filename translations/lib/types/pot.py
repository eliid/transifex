import os
from django.conf import settings
from translations.lib.types import (TransManagerMixin, TransManagerError)
from translations.models import POStatistic, Language

# I couldn't import this file from a separated dir
import libpo as po 

class POTStatsError(Exception):

    def __init__(self, lang):
        self.lang = lang

    def __str__(self):
        return "Could not calculate the statistics using the '%s' " \
               "language." % (self.lang)

class POTManager(TransManagerMixin):
    """ A browser class for POT files. """

    def __init__(self, file_set, path, source_lang):
        self.file_set = file_set
        self.path = path
        self.source_lang = source_lang

    def get_po_files(self):
        """ Return a list of PO filenames """

        po_files = []
        for filename in self.file_set:
            if filename.endswith('.po'):
                po_files.append(filename)
        po_files.sort()
        return po_files

    def get_langfile(self, lang):
        """ Return a PO filename """

        for filename in self.get_po_files():
            if os.path.basename(filename[:-3:]) == lang:
                return filename

    def get_langs(self):
        """ Return all langs tha have a po file for a component """

        langs = []
        for filename in self.get_po_files():
            langs.append(os.path.basename(filename[:-3:]))
        langs.sort()
        return langs

    def calcule_stats(self, lang):
        """ 
        Return the statistics of a specificy language for a 
        component 
        """
        try:
            file_path = os.path.join(self.path, self.get_langfile(lang))
            entries = po.read(file_path)
            return po.stats(entries)
        except AttributeError:
            raise POTStatsError, lang

    def create_stats(self, lang, component):
        """Set the statistics of a specificy language for a component."""
        try:
            stats = self.calcule_stats(lang)
            f = self.get_langfile(lang)
            s = POStatistic.objects.get(object_id=component.id, 
                                            filename=f)
        except POTStatsError:
            # TODO: It should probably be raised when a checkout of a 
            # module has a problem. Needs to decide what to do when it
            # happens
            pass
        except POStatistic.DoesNotExist:
            try:
                l = Language.objects.get(code=lang)
            except Language.DoesNotExist:
                l = None
            s = POStatistic.objects.create(lang=l, filename=f, 
                                           object=component)
        s.set_stats(trans=stats['translated'], fuzzy=stats['fuzzy'], 
                    untrans=stats['untranslated'])
        return s
