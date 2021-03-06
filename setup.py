#!/bin/python
import os
import sys
from pymongo import MongoClient
from bson.objectid import ObjectId

def modifyConfig(expression, value):
    print('Modifying '+expression+' with value '+str(value))
    os.system("sed -i 's/"+str(expression)+"/"+str(value)+"/' config.yml")

def main():

    mongoHosts = os.environ['mongo_addresses'].split(',')
    mongoDB = os.environ['mongo_database']
    mongoUsername = os.getenv('mongo_username', None)
    mongoPassword = os.getenv('mongo_password', None)

    client = MongoClient(mongoHosts)
    db = client[mongoDB]

    if mongoUsername is not None:
        db.authenticate(mongoUsername, mongoPassword)

    networksCollection = db['networks']
    bungeesCollection = db['bungees']
    bungeetypesCollection = db['bungeetypes']
    pluginsCollection = db['plugins']

    query = {"_id": ObjectId(os.environ['bungee_id'])}

    bungee = bungeesCollection.find_one(query)

    query = {"_id": ObjectId(bungee['bungee_type_id'])}

    bungeetype = bungeetypesCollection.find_one(query)

    query = {"_id": ObjectId(bungee['network_id'])}

    network = networksCollection.find_one(query)

    if bungeetype is None:
        print('No bungee type found')
        sys.exit(1)

    if network is None:
        print('No network found')
        sys.exit(1)

    plugins = []
    if 'plugins' in bungeetype:
        for pluginInfo in bungeetype['plugins']:
            plugin = pluginsCollection.find_one({"_id": ObjectId(pluginInfo['plugin_id'])})
            pluginConfig = None
            pluginVersion = None

            if 'configs' in plugin and 'pluginconfig_id' in pluginInfo:
                for config in plugin['configs']:
                    if config['_id'] == ObjectId(pluginInfo['pluginconfig_id']):
                        pluginConfig = config
                        break

            if 'versions' in plugin and 'pluginversion_id' in pluginInfo:
                for version in plugin['versions']:
                    if version['_id'] == ObjectId(pluginInfo['pluginversion_id']):
                        pluginVersion = version
                        break

            pluginDict = {'plugin': plugin, 'version': pluginVersion, 'config': pluginConfig}
            plugins.append(pluginDict)

    print('Copying Main Bungee files')
    os.system('cp -R /mnt/minestack/server/bungee/* .')

    os.system('mkdir plugins')
    for pluginInfo in plugins:
        plugin = pluginInfo['plugin']
        version = pluginInfo['version']
        config = pluginInfo['config']
        print('Copying plugin '+plugin['name'])

        if version is None:
            print('Plugin '+plugin['name']+' has no version. Skipping')
            continue

        if config is not None:
            os.system('mkdir plugins/'+plugin['directory'])
            os.system('cp -R /mnt/minestack/plugins/'+plugin['directory']+'/configs/'+config['directory']+'/* plugins/'+plugin['directory'])
        os.system('cp -R /mnt/minestack/plugins/'+plugin['directory']+'/versions/'+version['version']+'/* plugins')
    os.system('ls -l plugins')

    defaultServer = None
    for serverinfo in network['servertypes']:
        if serverinfo['defaultServerType']:
            defaultServer = serverinfo
            break

    if defaultServer is not None:
        modifyConfig("defaultserver", defaultServer['server_type_id'])
    else:
        print('No default server found')
        sys.exit(1)

    os.system('ls -l')

    os.system("chmod +x start.sh")
    os.system("./start.sh "+str(bungeetype['ram']))

main()
