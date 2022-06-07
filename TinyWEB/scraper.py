from pywebcopy import save_website

kwargs = {'project_name': 'some-fancy-name'}

save_website(
    url='http://192.168.5.12/part/AWS-Z-008660_rev_1/treeview',
    project_folder='erase',
    **kwargs
)