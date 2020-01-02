import sublime, sublime_plugin
import urllib.request
import json
import re


class JSDelivrAutocompletePlugin(sublime_plugin.EventListener):

    def on_query_completions(self, view, prefix, locations):
        loc = locations[0]

        if not view.score_selector(loc, "text"):
            return

        word = view.substr(view.word(loc))
        line = view.substr(view.line(loc))

        package = is_jsdelivr_package(line)

        if package:    
            return fetch_jsdelivr_complete(package)
        else:
            # @todo: Make it async
            return fetch_npm_complete(word)


def is_jsdelivr_package(line):
    match = re.search(r"cdn\.jsdelivr\.net\/npm\/([a-zA-Z0-9@\.\-]+)", line)

    if match:
        return match.group(1)

    return None


def fetch_jsdelivr_complete(package):
    req = urllib.request.Request(
        'https://data.jsdelivr.com/v1/package/npm/{}'.format(package)
    )
    req.add_header('User-Agent', 'jsDelivr sublime plugin (https://github.com/orn0t/jsdelivr-sublime-plugin)')

    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))

        comps = []
        
        if 'versions' in result:
            for v in result.get('versions', []):
                complete_str = "{}@{}".format(package, v)

                comps.append((complete_str, complete_str))
        elif 'files' in result:
            files = flatten_directories('', result['files'])
            
            for f in files:
                comps.append((f, f.strip('/')))

    return comps


def fetch_npm_complete(part):
    req = urllib.request.Request(
        'http://OFCNCOG2CU-dsn.algolia.net/1/indexes/npm-search/?attributesToRetrieve=name&query={}'.format(part)
    )
    req.add_header('X-Algolia-API-Key', 'f54e21fa3a2a0160595bb058179bfb1e')
    req.add_header('X-Algolia-Application-Id', 'OFCNCOG2CU')

    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))

        comps = []

        for hit in result['hits']:
            comps.append((
                "{}\t{}".format(hit['name'], "https://cdn.jsdelivr.net/npm/" + hit['name']),
                "https://cdn.jsdelivr.net/npm/" + hit['name']
            ))

    return comps


def flatten_directories(root, paths):
    results = []
    for path in paths:
        if path['type'] == 'directory':
            results.extend(flatten_directories(root + '/' + path['name'], path['files']))
        elif path['type'] == 'file':
            results.append(root + '/' + path['name'])

    return results

