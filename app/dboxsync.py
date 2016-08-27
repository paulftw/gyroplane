
import dropbox
from flask import session
from logging import info
from google.appengine.api import urlfetch

from secrets import DROPBOX_APP_KEY, DROPBOX_APP_SECRET

urlfetch.set_default_fetch_deadline(55)

def get_dropbox_flow():
    from app import SERVER_NAME
    return dropbox.client.DropboxOAuth2Flow(DROPBOX_APP_KEY, DROPBOX_APP_SECRET,
                                            redirect_uri="https://" + SERVER_NAME + "/dbo2",
                                            session=session,
                                            csrf_token_session_key="dropbox-auth-csrf")

def get_dropbox_client():
    if session.get('dbox-token') is None:
        return None
    return dropbox.client.DropboxClient(session.get('dbox-token'))


def get_fiddle_meta(fiddle_id):
    return get_dropbox_client().metadata('/' + fiddle_id)

"""
_igboe = {
    u'rev': u'63f9825a4', 
    u'hash': u'a7b89d3624946187831712ba0cbf3026', 
    u'size': u'0 bytes', 
    u'root': u'app_folder', 
    u'thumb_exists': False, 
    u'path': u'/1jfhodtasjk', 
    u'contents': [
        {
            u'rev': u'133f9825a4', 
            u'mime_type': u'text/html',
            u'size': u'85 bytes',
            u'root': u'app_folder',
            u'is_dir': False,
            u'thumb_exists': False,
            u'path': u'/1jfhodtasjk/counter.html',
            u'revision': 19,
            u'bytes': 85,
            u'client_mtime': u'Mon, 16 Nov 2015 23:04:20 +0000',
            u'icon': u'page_white_code',
            u'modified': u'Mon, 16 Nov 2015 23:04:20 +0000'
        },
        {
            u'rev': u'123f9825a4',
            u'mime_type': u'text/html',
            u'size': u'68 bytes',
            u'root': u'app_folder',
            u'is_dir': False,
            u'thumb_exists': False,
            u'path': u'/1jfhodtasjk/main.html',
            u'revision': 18,
            u'bytes': 68,
            u'client_mtime': u'Mon, 16 Nov 2015 23:04:15 +0000',
            u'icon': u'page_white_code',
            u'modified': u'Mon, 16 Nov 2015 23:04:15 +0000'
        },
        {
            u'rev': u'143f9825a4',
            u'mime_type': u'text/x-python',
            u'size': u'281 bytes',
            u'root': u'app_folder',
            u'is_dir': False,
            u'thumb_exists': False,
            u'path': u'/1jfhodtasjk/main.py',
            u'revision': 20,
            u'bytes': 281,
            u'client_mtime': u'Mon, 16 Nov 2015 23:04:32 +0000',
            u'icon': u'page_white_code',
            u'modified': u'Mon, 16 Nov 2015 23:04:32 +0000'
        }
    ],
    u'revision': 6,
    u'bytes': 0,
    u'is_dir': True,
    u'icon': u'folder',
    u'modified': u'Mon, 16 Nov 2015 22:13:30 +0000'
}"""

def get_folder_recursive(skipchars, path):
    client = get_dropbox_client()
    meta = client.metadata(path)

    res = []
    for f in meta['contents']:
        if f['is_dir']:
            res += get_folder_recursive(skipchars, f['path'])
        else:
            f['path'] = f['path'][skipchars:]
            res += [f]

    return res



def get_sync_state(fiddle_id, files):
    if fiddle_id is None:
        return ([],[],0)
    client = get_dropbox_client()
    if client is None:
        return ([],[],0)

    all_files = get_folder_recursive(len(fiddle_id)+2, '/' + fiddle_id)
    info('files = %s\n', '\n'.join(map(str, all_files)))

    dbox_newer = []

    stored_files = set(files.keys())
    total_files = len(stored_files)

    for df in all_files:
        path = df['path']
        stored_files.discard(path)
        if path not in files or files[path].get('dbox_revision',-1) < df[u'revision']:
            dbox_newer.append(path)

    dbox_missing = list(stored_files)
    return (dbox_newer, dbox_missing, total_files)


def load_from_dbox(fiddle_id, files):
    dbox_newer, dbox_missing, total_files = get_sync_state(fiddle_id, files)

    info('newer = %s,  missing = %s,  total = %s', dbox_newer, dbox_missing, total_files)

    deleted_files = {}
    for f in dbox_missing:
        deleted_files[f] = 1

    newer_files = {}
    client = get_dropbox_client()
    for fname in dbox_newer[:10]:
        resp, metadata = client.get_file_and_metadata('/%s/%s' % (fiddle_id, fname))
        newer_files[fname] = {
            'revision': metadata['revision'],
            'content': resp.read(),
        }
        resp.close()
    import fiddler

    info ('write = ne %s,  del=%s', newer_files.keys(), deleted_files.keys())

    return fiddler.save_app(newer_files, deleted_files, fiddle_id, client)

