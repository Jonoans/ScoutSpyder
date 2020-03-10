import multiprocessing.managers
import os

BACKUP_AUTOPROXY = multiprocessing.managers.AutoProxy

def PATCHED_AUTOPROXY(token, serializer,
    manager=None, authkey=None, exposed=None,
    incref=True, manager_owned=True):
    return BACKUP_AUTOPROXY(token, serializer,
        manager, authkey, exposed, incref)

def patch_autoproxy():
    global multiprocessing
    if os.name == 'posix':
        multiprocessing.managers.AutoProxy = PATCHED_AUTOPROXY