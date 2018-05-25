import upip
from upip import url_open, simple_lst_re

orig_get_latest_url_simple = upip.get_latest_url_simple

def get_latest_url_simple(name):
    """ this is modified version of get_latest_url_simple from upip package. 
    In this version, name can contain version specification """
    version = None
    if "==" in name:
        name, version = name.split("==")
        vername = "%s-%s" % (name, version)
        print("name=%s version=%s vername=%s" % (name, version, vername))

    # Stupid PEP 503 normalization
    name = name.replace("_", "-").replace(".", "-").lower()
    f = url_open("https://pypi.org/simple/%s/" % name)
    try:
        last_url = None
        while 1:
            l = f.readline().decode()
            if not l: break
            m = simple_lst_re.search(l)
            if m:
                last_url = m.group(1)
                
                # print("considering url=", last_url, "vername in last_url=", (vername in last_url))
                if version and vername in last_url:
                    return last_url
        return last_url
    finally:
        f.close()

upip.get_latest_url_simple = get_latest_url_simple

