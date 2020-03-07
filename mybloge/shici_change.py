import os,random
oldfiledir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shici')
dirlist = os.listdir(oldfiledir)
old_file_path = os.path.join(oldfiledir, dirlist[random.randint(0, len(dirlist) - 1)])
with open(old_file_path,'rb') as fold:
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates', 'shici.html'), 'wb') as newf:
        newf.write(fold.read())
