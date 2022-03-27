import urllib.request
from urllib.error import HTTPError
import json
import jwt
import discord
import asyncio
import requests
from discord import Webhook, RequestsWebhookAdapter
import random

#  Boylan Heights Clan API Token: ma73n9y9
secret = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6IjY0YjI4MzNlLWYyNWUtNDk4MC04Yzk3LTJkN2ZjOTEzYjE0OCIsImlhdCI6MTYzOTQxODUwMCwic3ViIjoiZGV2ZWxvcGVyL2JiN2Q5YjM4LWQ0YmItNTg3NC03NzMzLTVmMWE0NDA1OTk3MSIsInNjb3BlcyI6WyJyb3lhbGUiXSwibGltaXRzIjpbeyJ0aWVyIjoiZGV2ZWxvcGVyL3NpbHZlciIsInR5cGUiOiJ0aHJvdHRsaW5nIn0seyJjaWRycyI6WyI5OC4xMTUuMTA4LjIyIl0sInR5cGUiOiJjbGllbnQifV19.Ma1-rpa6oLLatcf9oOJ6cuiZuJeNAKn-aLqFHISoOB2Q54SS_h90p6SYeqDw8t2hkHVu3aEDRWYi6XCaWWxtBA"
clanTag = "PL9VVL8R"  # Boylan Heights Clan Tag
baseUrl = "https://api.clashroyale.com/v1"


#  ------------------ Methods/Functions -------------------------
def get_request(endpoint):
    r = urllib.request.Request(
            baseUrl + endpoint,
            None,
            {
                "Authorization": "Bearer %s" % secret
            }
        )
    return r


def get_player_nametags():
    player_nametags = []
    endpoint = "/clans/%23PL9VVL8R/members"
    r = get_request(endpoint)
    response = urllib.request.urlopen(r).read().decode("utf-8")
    data = json.loads(response)
    for item in data["items"]:
        name = "%s" % (item['name'])
        tag = "%s" % (item["tag"])
        temp = [name, tag]
        player_nametags.append(temp)
    return player_nametags


def get_ranks():
    discord_message = ''
    endpoint = "/clans/%23PL9VVL8R/members"
    r = get_request(endpoint)
    response = urllib.request.urlopen(r).read().decode("utf-8")
    data = json.loads(response)
    for item in data["items"]:
        discord_message += "%d.) [%d] %s %s\n" % (item["clanRank"], item["trophies"], item["tag"], item["name"])
    return discord_message


def get_player_info(player_name):
    discord_message = ''
    player_nametags = get_player_nametags()
    player_exists = 0
    for i in player_nametags:
        if i[0] == player_name:
            player_exists = 1
            tag = i[1]
    if player_exists == 0:
        return "--PLAYER NOT IN CLAN-- \n *case sensitive check spelling*"
    endpoint = "/players/{}/members".format(tag)
    print(endpoint)
    r = get_request(endpoint)
    response = urllib.request.urlopen(r).read().decode("utf-8")
    print(response)
    data = json.loads(response)
    #  for item in data["items"]:
    return "--Player is in Clan Test Successful!--"


def get_scores():
    endpoint = "/clans/%23{}/riverracelog".format(clanTag)
    r = get_request(endpoint)
    response = urllib.request.urlopen(r).read().decode("utf-8")
    data = json.loads(response)
    current_season = 0
    section_index = -1
    current_index = -1
    i = 0
    for item in data["items"]:
        if item["seasonId"] > current_season:
            current_season = item["seasonId"]
            if item["sectionIndex"] > current_index:
                current_index = i
        i += 1
    this_war = data["items"][current_index]['standings']
    fame = 0
    decks_used = 0
    donations = 0
    trophies = 0
    exp_level = 0
    donations_received = 0
    clan_scores = {}
    name_list = []
    player_nametags = get_player_nametags()
    for player in player_nametags:
        name_list.append(player[0])
    for item in this_war:
        if item['clan']['name'] == "Boylan Heights":
            for player in item['clan']['participants']:
                name = player['name']
                fame = player['fame']
                decks_used = player['decksUsed']
                tag = player['tag'][1:]
                endpoint = "/players/%23{}/".format(tag)
                r = get_request(endpoint)
                try:
                    response = urllib.request.urlopen(r).read().decode("utf-8")
                except HTTPError as err:
                    if err.code == 404:
                        print("ERROR -- Cannot Find Player %s %s Account" % (name, tag))
                data = json.loads(response)
                donations = data['donations']
                trophies = data['trophies']
                exp_level = data['expLevel']
                donations_received = data['donationsReceived']
                if donations >= 100:
                    donation_score = 25
                else:
                    donation_score = (donations/100)*25
                score = ((fame/3200)*75) + donation_score
                if name in name_list:
                    clan_scores[name] = score
    sorted_clan_scores = sorted(clan_scores.items(), key=lambda x: x[1], reverse=True)
    discord_message = ''
    for i in sorted_clan_scores:
        discord_message += '['+ str(i[1]) +'] '+ str(i[0]) + '\n'
    return discord_message


#  ------------------- Discord Bot Controls ---------------------


#  Clash Royale Discord Bot Token
token = "ODU2MjU5ODY4NzE3NzQ0MTg5.YM-cJQ.Io0WePr4tSWQA_bYCzjfOi0c88k"
#  Clash Royale Discord Webhook Url
webhook = Webhook.from_url("https://discord.com/api/webhooks/856254699393122335/ClhhbC6ISAn_OmJEyzwQRRB9l7gy1p8MR8x2dJZXkdT902Z7u1K6mvRK4hXfPNJmke0F",adapter=RequestsWebhookAdapter())

client = discord.Client()
channel = client.get_channel(829371670543728680)


@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')


@client.event
async def on_message(message):
    discord_message = ''
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        discord_message = 'Hello, test complete'
        await message.channel.send(discord_message)

    if message.content.startswith('$help'):
        discord_message = 'Clash Royale Bot Commands:\n'
        discord_message += '$ranks :\n'
        discord_message += '        Prints the current rank, trophy, player tag and username of each Boylan Heights clan member.\n'
        discord_message += '$playerinfo {INSERT PLAYER NAME}:\n'
        discord_message += '        Prints player info for the specified player (no curlies)\n'
        discord_message += '$scores :\n'
        discord_message += '        Generates a list of Boylan Heights most recent clan war participants with a calculated score based on card donations and fame acquired during the war (does not include wars currently in progress).\n'
        # discord_message += '$ :\n'
        # discord_message += '        .\n'
        await message.channel.send(discord_message)

    if message.content.startswith('$ranks'):
        discord_message = get_ranks()
        await message.channel.send(discord_message)

    if message.content.startswith('$playerinfo '):
        player_name = message.content[12:]
        discord_message = get_player_info(player_name)
        await message.channel.send(discord_message)

    if message.content.startswith('$scores'):
        discord_message = get_scores()
        await message.channel.send(discord_message)

#  comment out to test a new url
client.run(token)


#  -------------TEST NEW URL --------------------#
def test_new_url():
    endpoint = "/clans/%23{}/riverracelog".format(clanTag)
    r = get_request(endpoint)
    response = urllib.request.urlopen(r).read().decode("utf-8")
    #print(response)
    data = json.loads(response)
    message = ''
    current_season = 0
    section_index = -1
    created_date = ''
    current_index = -1
    i = 0
    for item in data["items"]:
        if item["seasonId"] > current_season:
            current_season = item["seasonId"]
            if item["sectionIndex"] > current_index:
                section_index = item["sectionIndex"]
                created_date = item["createdDate"]
                current_index = i
        message += "Season ID: %d        Section Index: %d        Created Date: %s\n" % (item["seasonId"], item["sectionIndex"], item["createdDate"])
        i += 1

    #print(message)
    this_war = data["items"][current_index]['standings']
    player_war_info = ''
    fame = 0
    decks_used = 0
    dontations = 0
    trophies = 0
    exp_level = 0
    donations_received = 0
    clan_scores = {}
    for item in this_war:
        if item['clan']['name'] == "Boylan Heights":
            for player in item['clan']['participants']:
                name = player['name']
                fame = player['fame']
                decks_used = player['decksUsed']
                tag = player['tag'][1:]
                #print(name + ":" + tag)
                endpoint = "/players/%23{}/".format(tag)
                r = get_request(endpoint)
                try:
                    response = urllib.request.urlopen(r).read().decode("utf-8")
                except HTTPError as err:
                    if err.code == 404:
                        print("ERROR -- Cannot Find Player %s %s Account" % (name, tag))

                data = json.loads(response)
                donations = data['donations']
                trophies = data['trophies']
                exp_level = data['expLevel']
                donations_received = data['donationsReceived']
                if donations >= 100:
                    donation_score = 25
                else:
                    donation_score = (donations/100)*25
                score = ((fame/3200)*75) + donation_score
                clan_scores[name] = score

                #  player_war_info += '%s :%s   Fame: %d  Number of Decks Used: %d \n'% (player['name'], player['tag'], player['fame'], player['decksUsed'])
    sorted_clan_scores = sorted(clan_scores.items(), key=lambda x: x[1], reverse=True)
    i=0
    discord_message = ''
    for i in sorted_clan_scores:
        discord_message += '['+ str(i[1]) +'] '+ str(i[0]) + '\n'
    # print("Current War Season ID: " + str(current_season) + " Current War Week Index: " + str(section_index) + " Current Json Index: " + str(current_index))

    return discord_message
    #print(player_war_info)


#test_new_url()


