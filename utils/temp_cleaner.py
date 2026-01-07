import os
import sys
import shutil
import time


RUNTIME_TMPDIR = r'C:\LLBotTemp'


def cleanup_pyinstaller_temp():
    if not getattr(sys, 'frozen', False):
        return
    
    if not os.path.exists(RUNTIME_TMPDIR):
        return
    
    current_mei = getattr(sys, '_MEIPASS', None)
    current_mei_name = os.path.basename(current_mei) if current_mei else None
    
    now = time.time()
    for item in os.listdir(RUNTIME_TMPDIR):
        if not item.startswith('_MEI'):
            continue
        if item == current_mei_name:
            continue
        
        item_path = os.path.join(RUNTIME_TMPDIR, item)
        if not os.path.isdir(item_path):
            continue
        
        try:
            if (now - os.path.getmtime(item_path)) < 3600:
                continue
        except:
            continue
        
        # 通过重命名检测目录是否被其他进程占用
        test_path = item_path + '_test_delete'
        try:
            os.rename(item_path, test_path)
            os.rename(test_path, item_path)
            shutil.rmtree(item_path, ignore_errors=True)
        except OSError:
            pass
