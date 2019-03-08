# encoding: utf-8
import sys
from workflow import Workflow3, web, ICON_WARNING, ICON_ERROR

log = None
nrid = None
nrkey = None

def require_setup(wf):
    if nrid is None:
        wf.add_item(
            "must supply a new relic id: nr_id",
            icon=ICON_ERROR)
    if nrkey is None:
        wf.add_item(
            "must supply a new relic api key: nr_key",
            icon=ICON_ERROR)
    if len(wf._items) > 0:
        wf.send_feedback()
        sys.exit(1)

def get_apps(wf):
    apps = wf.stored_data("apps")
    if apps is not None:
        return apps
    r = web.get('https://api.newrelic.com/v2/applications.json', headers={'X-Api-Key': nrkey})
    r.raise_for_status()
    apps = r.json()['applications']
    apps = list(filter(lambda app: app['health_status'] == 'orange' or app['health_status'] == 'red' or app['health_status'] == 'green', apps))
    wf.store_data('apps', apps)
    return apps

def main(wf):
    args = wf.args
    keyword = args[0]

    if keyword == '--id':
        wf.store_data("id", args[1])
        return
    elif keyword == '--key':
        wf.store_data("key", args[1])
        return
    elif keyword == '--app':
        log.debug("ARGS LENGTH: ")
        log.debug(len(args))
        log.debug("^^^^^")
        require_setup(wf)
        apps = get_apps(wf)
        if len(args) > 1:
            query = " ".join(args[1:])
            apps = wf.filter(query, apps, key=lambda app: app['name'])
            if not apps:
                wf.add_item('No matching app found', 'Try a different query', icon=ICON_WARNING)
                wf.send_feedback()
                return
        for app in apps:
            url = 'https://rpm.newrelic.com/accounts/%s/applications/%d' % (nrid, app['id'])
            wf.add_item(
                app['name'],
                subtitle='ID: %d | Language: %s' % (app['id'], app['language']),
                arg=url,
                valid=True,
                uid=url
            )
        wf.send_feedback()
        return
    elif keyword == '--refresh':
        wf.clear_data(lambda f: 'apps' in f)
        get_apps(wf)

if __name__ == u"__main__":
    wf = Workflow3(libraries=['./lib'])
    log = wf.logger
    nrid = wf.stored_data('id')
    nrkey = wf.stored_data('key')
    sys.exit(wf.run(main))