#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
#
#   PYTHON MODULE:     MKI18N.PY
#                      =========
#
#   Abstract:         Make Internationalization (i18n) files for an application.
#
#   Copyright Pierre Rouleau. 2003. Released to public domain.
#
#   Last update: Saturday, November 8, 2003. @ 15:55:18.
#
#   File: ROUP2003N01::C:/dev/python/mki18n.py
#
#   RCS $Header: //software/official/MKS/MKS_SI/TV_NT/dev/Python/rcs/mki18n.py 1.5 2003/11/05 19:40:04 PRouleau Exp $
#
#   Update history:
#
#   - File created: Saturday, June 7, 2003. by Pierre Rouleau
#   - 10/06/03 rcs : RCS Revision 1.1  2003/06/10 10:06:12  PRouleau
#   - 10/06/03 rcs : RCS Initial revision
#   - 23/08/03 rcs : RCS Revision 1.2  2003/06/10 10:54:27  PRouleau
#   - 23/08/03 P.R.: [code:fix] : The strings encoded in this file are encode in iso-8859-1 format.  Added the encoding
#                    notification to Python to comply with Python's 2.3 PEP 263.
#   - 23/08/03 P.R.: [feature:new] : Added the '-e' switch which is used to force the creation of the empty English .mo file.
#   - 22/10/03 P.R.: [code] : incorporated utility functions in here to make script self sufficient.
#   - 05/11/03 rcs : RCS Revision 1.4  2003/10/22 06:39:31  PRouleau
#   - 05/11/03 P.R.: [code:fix] : included the unixpath() in this file.
#   - 08/11/03 rcs : RCS Revision 1.5  2003/11/05 19:40:04  PRouleau
#
#   RCS $Log: $
#
#
# -----------------------------------------------------------------------------
"""
mki18n allows you to internationalize your software.  You can use it to
create the GNU .po files (Portable Object) and the compiled .mo files
(Machine Object).

mki18n module can be used from the command line or from within a script (see
the Usage at the end of this page).

    Table of Contents
    -----------------

    makePO()             -- Build the Portable Object file for the application --
    catPO()              -- Concatenate one or several PO files with the application domain files. --
    makeMO()             -- Compile the Portable Object files into the Machine Object stored in the right location. --
    printUsage           -- Displays how to use this script from the command line --

    Scriptexecution      -- Runs when invoked from the command line --


NOTE:  this module uses GNU gettext utilities.

You can get the gettext tools from the following sites:

   - `GNU FTP site for gettetx`_ where several versions (0.10.40, 0.11.2, 0.11.5 and 0.12.1) are available.
     Note  that you need to use `GNU libiconv`_ to use this. Get it from the `GNU
     libiconv  ftp site`_ and get version 1.9.1 or later. Get the Windows .ZIP
     files and install the packages inside c:/gnu. All binaries will be stored
     inside  c:/gnu/bin.  Just  put c:/gnu/bin inside your PATH. You will need
     the following files:

      - `gettext-runtime-0.12.1.bin.woe32.zip`_
      - `gettext-tools-0.12.1.bin.woe32.zip`_
      - `libiconv-1.9.1.bin.woe32.zip`_


.. _GNU libiconv:                            http://www.gnu.org/software/libiconv/
.. _GNU libiconv ftp site:                   http://www.ibiblio.org/pub/gnu/libiconv/
.. _gettext-runtime-0.12.1.bin.woe32.zip:    ftp://ftp.gnu.org/gnu/gettext/gettext-runtime-0.12.1.bin.woe32.zip
.. _gettext-tools-0.12.1.bin.woe32.zip:      ftp://ftp.gnu.org/gnu/gettext/gettext-tools-0.12.1.bin.woe32.zip
.. _libiconv-1.9.1.bin.woe32.zip:            http://www.ibiblio.org/pub/gnu/libiconv/libiconv-1.9.1.bin.woe32.zip

"""
# -----------------------------------------------------------------------------
# Module Import
# -------------
#

from __future__ import absolute_import
from __future__ import print_function
import os
import sys
import re
from builtins import str as text
import wx


# -----------------------------------------------------------------------------
# Global variables
# ----------------
#

__author__ = "Pierre Rouleau"
__version__ = "$Revision: 1.5 $"

# -----------------------------------------------------------------------------


def getSupportedLanguageDict(appname):
    """
    Returns dictionary with languages already supported
    by given application

    param: appname:
        name of application
    """
    languageDict = {}
    ext = '.po'
    files = [x for x in os.listdir('.')
             if x.startswith(appname) and x.endswith(ext)]

    langs = [x.split(appname + '_')[1].split(ext)[0] for x in files]
    for lang in langs:
        languageDict[lang] = lang

    return languageDict


def getlanguageDict():
    languageDict = {}
    getSupportedLanguageDict('Beremiz')
    if wx.VERSION >= (3, 0, 0):
        _app = wx.App()
    else:
        _app = wx.PySimpleApp()

    for lang in [x for x in dir(wx) if x.startswith("LANGUAGE")]:
        i = wx.Locale(wx.LANGUAGE_DEFAULT).GetLanguageInfo(getattr(wx, lang))
        if i:
            languageDict[i.CanonicalName] = i.Description

    return languageDict


def verbosePrint(verbose, str):
    if verbose:
        print(str)


def processCustomFiles(filein, fileout, regexp, prefix=''):
    appfil_file = open(filein, 'r')
    messages_file = open(fileout, 'r')
    messages = messages_file.read()
    messages_file.close()
    messages_file = open(fileout, 'a')
    messages_file.write('\n')
    messages_file.write('#: %s\n' % prefix)
    messages_file.write('\n')

    words_found = {}
    for filepath in appfil_file.readlines():
        code_file = open(filepath.strip(), 'r')
        for match in regexp.finditer(code_file.read()):
            word = match.group(1)
            if not words_found.get(word, False) and messages.find("msgid \"%s\"\nmsgstr \"\"" % word) == -1:
                words_found[word] = True
                messages_file.write('\n')
                messages_file.write("msgid \"%s\"\n" % word)
                messages_file.write("msgstr \"\"\n")
        code_file.close()

    messages_file.close()
    appfil_file.close()


# -----------------------------------------------------------------------------
# m a k e P O ( )         -- Build the Portable Object file for the application --
# ^^^^^^^^^^^^^^^
#
def makePO(applicationDirectoryPath,  applicationDomain=None, verbose=0):
    """Build the Portable Object Template file for the application.

    makePO builds the .pot file for the application stored inside
    a specified directory by running xgettext for all application source
    files.  It finds the name of all files by looking for a file called 'app.fil'.
    If this file does not exists, makePo raises an IOError exception.
    By default the application domain (the application
    name) is the same as the directory name but it can be overridden by the
    'applicationDomain' argument.

    makePO always creates a new file called messages.pot.  If it finds files
    of the form app_xx.po where 'app' is the application name and 'xx' is one
    of the ISO 639 two-letter language codes, makePO resynchronizes those
    files with the latest extracted strings (now contained in messages.pot).
    This process updates all line location number in the language-specific
    .po files and may also create new entries for translation (or comment out
    some).  The .po file is not changed, instead a new file is created with
    the .new extension appended to the name of the .po file.

    By default the function does not display what it is doing.  Set the
    verbose argument to 1 to force it to print its commands.
    """

    if applicationDomain is None:
        applicationName = fileBaseOf(applicationDirectoryPath, withPath=0)
    else:
        applicationName = applicationDomain
    currentDir = os.getcwd()
    os.chdir(applicationDirectoryPath)
    filelist = 'app.fil'
    if not os.path.exists(filelist):
        raise IOError(2, 'No module file: %s' % filelist)

    fileout = 'messages.pot'
    # Steps:
    #  Use xgettext to parse all application modules
    #  The following switches are used:
    #
    #   -s                          : sort output by string content (easier to use when we need to merge several .po files)
    #   --files-from=app.fil        : The list of files is taken from the file: app.fil
    #   --output=                   : specifies the name of the output file (using a .pot extension)
    cmd = 'xgettext -s --no-wrap --language=Python --files-from=' + filelist + ' --output=' + fileout + ' --package-name ' + applicationName
    verbosePrint(verbose, cmd)
    os.system(cmd)

    XSD_STRING_MODEL = re.compile(r"<xsd\:(?:element|attribute) name=\"([^\"]*)\"[^\>]*\>")
    processCustomFiles(filelist, fileout, XSD_STRING_MODEL, 'Extra XSD strings')

    XML_TC6_STRING_MODEL = re.compile(r"<documentation>\s*<xhtml\:p><!\[CDATA\[([^\]]*)\]\]></xhtml\:p>\s*</documentation>", re.MULTILINE | re.DOTALL)
    processCustomFiles(filelist, fileout, XML_TC6_STRING_MODEL, 'Extra TC6 documentation strings')

    # generate messages.po
    cmd = 'msginit --no-wrap --no-translator -i %s -l en_US.UTF-8 -o messages.po' % (fileout)
    verbosePrint(verbose, cmd)
    os.system(cmd)

    languageDict = getSupportedLanguageDict(applicationName)

    for langCode in languageDict.keys():
        if langCode == 'en':
            pass
        else:
            langPOfileName = "%s_%s.po" % (applicationName, langCode)
            if os.path.exists(langPOfileName):
                cmd = 'msgmerge -s --no-wrap "%s" %s > "%s.new"' % (langPOfileName, fileout, langPOfileName)
                verbosePrint(verbose, cmd)
                os.system(cmd)
    os.chdir(currentDir)


def catPO(applicationDirectoryPath, listOf_extraPo, applicationDomain=None, targetDir=None, verbose=0):
    """Concatenate one or several PO files with the application domain files.
    """

    if applicationDomain is None:
        applicationName = fileBaseOf(applicationDirectoryPath, withPath=0)
    else:
        applicationName = applicationDomain
    currentDir = os.getcwd()
    os.chdir(applicationDirectoryPath)

    languageDict = getSupportedLanguageDict(applicationName)

    for langCode in languageDict.keys():
        if langCode == 'en':
            pass
        else:
            langPOfileName = "%s_%s.po" % (applicationName, langCode)
            if os.path.exists(langPOfileName):
                fileList = ''
                for fileName in listOf_extraPo:
                    fileList += ("%s_%s.po " % (fileName, langCode))
                cmd = "msgcat -s --no-wrap %s %s > %s.cat" % (langPOfileName, fileList, langPOfileName)
                verbosePrint(verbose, cmd)
                os.system(cmd)
                if targetDir is None:
                    pass
                else:
                    mo_targetDir = "%s/%s/LC_MESSAGES" % (targetDir, langCode)
                    cmd = "msgfmt --output-file=%s/%s.mo %s_%s.po.cat" % (mo_targetDir, applicationName, applicationName, langCode)
                    verbosePrint(verbose, cmd)
                    os.system(cmd)
    os.chdir(currentDir)


def makeMO(applicationDirectoryPath, targetDir='./locale', applicationDomain=None, verbose=0, forceEnglish=0):
    """Compile the Portable Object files into the Machine Object stored in the right location.

    makeMO converts all translated language-specific PO files located inside
    the  application directory into the binary .MO files stored inside the
    LC_MESSAGES sub-directory for the found locale files.

    makeMO searches for all files that have a name of the form 'app_xx.po'
    inside the application directory specified by the first argument.  The
    'app' is the application domain name (that can be specified by the
    applicationDomain argument or is taken from the directory name). The 'xx'
    corresponds to one of the ISO 639 two-letter language codes.

    makeMo stores the resulting files inside a sub-directory of `targetDir`
    called xx/LC_MESSAGES where 'xx' corresponds to the 2-letter language
    code.
    """

    if targetDir is None:
        targetDir = './locale'

    verbosePrint(verbose, "Target directory for .mo files is: %s" % targetDir)

    if applicationDomain is None:
        applicationName = fileBaseOf(applicationDirectoryPath, withPath=0)
    else:
        applicationName = applicationDomain
    currentDir = os.getcwd()
    os.chdir(applicationDirectoryPath)

    languageDict = getSupportedLanguageDict(applicationName)

    for langCode in languageDict.keys():
        if (langCode == 'en') and (forceEnglish == 0):
            pass
        else:
            langPOfileName = "%s_%s.po" % (applicationName, langCode)
            if os.path.exists(langPOfileName):
                mo_targetDir = "%s/%s/LC_MESSAGES" % (targetDir, langCode)
                if not os.path.exists(mo_targetDir):
                    mkdir(mo_targetDir)
                cmd = 'msgfmt --output-file="%s/%s.mo" "%s_%s.po"' % (mo_targetDir, applicationName, applicationName, langCode)
                verbosePrint(verbose, cmd)
                os.system(cmd)
    os.chdir(currentDir)


def printUsage(errorMsg=None):
    """Displays how to use this script from the command line."""
    print("""
    ##################################################################################
    #   mki18n :   Make internationalization files.                                  #
    #              Uses the GNU gettext system to create PO (Portable Object) files  #
    #              from source code, coimpile PO into MO (Machine Object) files.     #
    #              Supports C,C++,Python source files.                               #
    #                                                                                #
    #   Usage: mki18n {OPTION} [appDirPath]                                          #
    #                                                                                #
    #   Options:                                                                     #
    #     -e               : When -m is used, forces English .mo file creation       #
    #     -h               : prints this help                                        #
    #     -m               : make MO from existing PO files                          #
    #     -p               : make PO, update PO files: Creates a new messages.pot    #
    #                        file. Creates a dom_xx.po.new for every existing        #
    #                        language specific .po file. ('xx' stands for the ISO639 #
    #                        two-letter language code and 'dom' stands for the       #
    #                        application domain name).  mki18n requires that you     #
    #                        write a 'app.fil' file  which contains the list of all  #
    #                        source code to parse.                                   #
    #     -v               : verbose (prints comments while running)                 #
    #     --domain=appName : specifies the application domain name.  By default      #
    #                        the directory name is used.                             #
    #     --moTarget=dir : specifies the directory where .mo files are stored.       #
    #                      If not specified, the target is './locale'                #
    #                                                                                #
    #   You must specify one of the -p or -m option to perform the work.  You can    #
    #   specify the path of the target application.  If you leave it out mki18n      #
    #   will use the current directory as the application main directory.            #
    #                                                                                #
    ##################################################################################""")
    if errorMsg:
        print("\n   ERROR: %s" % errorMsg)


def fileBaseOf(filename, withPath=0):
    """fileBaseOf(filename,withPath) ---> string

    Return base name of filename.  The returned string never includes the extension.
    Use os.path.basename() to return the basename with the extension.  The
    second argument is optional.  If specified and if set to 'true' (non zero)
    the string returned contains the full path of the file name.  Otherwise the
    path is excluded.

    [Example]
    >>> fn = 'd:/dev/telepath/tvapp/code/test.html'
    >>> fileBaseOf(fn)
    'test'
    >>> fileBaseOf(fn)
    'test'
    >>> fileBaseOf(fn,1)
    'd:/dev/telepath/tvapp/code/test'
    >>> fileBaseOf(fn,0)
    'test'
    >>> fn = 'abcdef'
    >>> fileBaseOf(fn)
    'abcdef'
    >>> fileBaseOf(fn,1)
    'abcdef'
    >>> fn = "abcdef."
    >>> fileBaseOf(fn)
    'abcdef'
    >>> fileBaseOf(fn,1)
    'abcdef'
    """
    pos = filename.rfind('.')
    if pos > 0:
        filename = filename[:pos]
    if withPath:
        return filename
    else:
        return os.path.basename(filename)


def mkdir(directory):
    """Create a directory (and possibly the entire tree).

    The os.mkdir() will fail to create a directory if one of the
    directory in the specified path does not exist.  mkdir()
    solves this problem.  It creates every intermediate directory
    required to create the final path. Under Unix, the function
    only supports forward slash separator, but under Windows and MacOS
    the function supports the forward slash and the OS separator (backslash
    under windows).
    """

    # translate the path separators
    directory = unixpath(directory)
    # build a list of all directory elements
    aList = filter(lambda x: len(x) > 0, directory.split('/'))
    theLen = len(aList)
    # if the first element is a Windows-style disk drive
    # concatenate it with the first directory
    if aList[0].endswith(':'):
        if theLen > 1:
            aList[1] = aList[0] + '/' + aList[1]
            del aList[0]
            theLen -= 1
    # if the original directory starts at root,
    # make sure the first element of the list
    # starts at root too
    if directory[0] == '/':
        aList[0] = '/' + aList[0]
    # Now iterate through the list, check if the
    # directory exists and if not create it
    theDir = ''
    for i in range(theLen):
        theDir += aList[i]
        if not os.path.exists(theDir):
            os.mkdir(theDir)
        theDir += '/'


def unixpath(thePath):
    r"""Return a path name that contains Unix separator.

    [Example]
    >>> unixpath(r"d:\test")
    'd:/test'
    >>> unixpath("d:/test/file.txt")
    'd:/test/file.txt'
    >>>
    """
    thePath = os.path.normpath(thePath)
    if os.sep == '/':
        return thePath
    else:
        return thePath.replace(os.sep, '/')


# -----------------------------------------------------------------------------

# S c r i p t   e x e c u t i o n               -- Runs when invoked from the command line --
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
if __name__ == "__main__":
    # command line parsing
    import getopt    # pylint: disable=wrong-import-order,wrong-import-position
    argc = len(sys.argv)
    if argc == 1:
        printUsage('Missing argument: specify at least one of -m or -p (or both).')
        sys.exit(1)
    # If there is some arguments, parse the command line
    validOptions = "ehmpv"
    validLongOptions = ['domain=', 'moTarget=']
    option = {}
    option['forceEnglish'] = 0
    option['mo'] = 0
    option['po'] = 0
    option['verbose'] = 0
    option['domain'] = None
    option['moTarget'] = None
    optionKey = {
        '-e':         'forceEnglish',
        '-m':         'mo',
        '-p':         'po',
        '-v':         'verbose',
        '--domain':   'domain',
        '--moTarget': 'moTarget',
    }
    exit_code = 1
    try:
        optionList, pargs = getopt.getopt(sys.argv[1:], validOptions, validLongOptions)
    except getopt.GetoptError as e:
        printUsage(e)
        sys.exit(1)
    for (opt, val) in optionList:
        if opt == '-h':
            printUsage()
            sys.exit(0)
        option[optionKey[opt]] = 1 if val == '' else val
    if len(pargs) == 0:
        appDirPath = os.getcwd()
        if option['verbose']:
            print("No project directory given. Using current one:  %s" % appDirPath)
    elif len(pargs) == 1:
        appDirPath = pargs[0]
    else:
        printUsage('Too many arguments (%u).  Use double quotes if you have space in directory name' % len(pargs))
        sys.exit(1)
    if option['domain'] is None:
        # If no domain specified, use the name of the target directory
        option['domain'] = fileBaseOf(appDirPath)
    if option['verbose']:
        print("Application domain used is: '%s'" % option['domain'])
    if option['po']:
        try:
            makePO(appDirPath, option['domain'], option['verbose'])
            exit_code = 0
        except IOError as e:
            printUsage(text(e) + '\n   You must write a file app.fil that contains the list of all files to parse.')
    if option['mo']:
        makeMO(appDirPath, option['moTarget'], option['domain'], option['verbose'], option['forceEnglish'])
        exit_code = 0
    sys.exit(exit_code)


# -----------------------------------------------------------------------------
