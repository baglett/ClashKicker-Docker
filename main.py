import urllib.request
import json
import os
import pymysql
from dotenv import load_dotenv
import schedule
from datetime import date
from datetime import datetime
import time
import urllib.request

# manage environment variables
load_dotenv()

# database connection .env variables
db_host = os.getenv('HOST')
db_user = os.getenv('DB_USER')
db_pass = os.getenv('DB_PASS')

# weekdays as a tuple
weekDays = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")

# API Information
baseUrl = "https://api.clashroyale.com/v1"
clan_tag = os.getenv('CLAN_TAG')
clan_secret = os.getenv('CLAN_SECRET')


# connect to mysql database
def mysqlconnect():
    # To connect MySQL database
    connection = pymysql.connect(
        host=db_host,
        user=db_user,
        password=db_pass,
        db='hello_mysql',
    )
    return connection


def get_request(endpoint):
    r = urllib.request.Request(baseUrl + endpoint, None, {"Authorization": "Bearer %s" % clan_secret})
    return r


def scrape_clan_data():
    player_clan_data = scrape_player_clan_data()  # json format, list of dicts
    for player in player_clan_data:
        #print(player_clan_data[player]["tag"])
        player_specific_data = scrape_player_specific_data(player_clan_data[player]["tag"])
        player_clan_data[player].update(player_specific_data)
        #print(player_specific_data)
        # add all player specific data values to existing player_clan_data by referencing the player tag
        # for item in player_specific_data:
        #    i = i + 1
            #player.update()
    return player_clan_data


def scrape_player_specific_data(player_tag):
    endpoint = "/players/%23{}".format(player_tag)
    r = get_request(endpoint)
    response = urllib.request.urlopen(r).read().decode("utf-8")
    data = json.loads(response)
    player_specific_data = {
        "name": data["name"],
        "role": data["role"],
        "xp_level": data["expLevel"],
        "trophies": data["bestTrophies"],
        "arena_id": data["arena"]["id"],
        "arena_name": data["arena"]["name"],
        "donations": data["donations"],
        "donation_received": data["donationsReceived"],
        "trophy_high": data["bestTrophies"],
        "total_wins": data["wins"],
        "total_losses": data["losses"],
        "battle_count": data["battleCount"],
        "three_crown_wins": data["threeCrownWins"],
        "challenge_cards_won": data["challengeCardsWon"],
        "challenge_max_wins": data["challengeMaxWins"],
        "tourney_cards_won": data["tournamentCardsWon"],
        "tourney_battle_count": data["tournamentBattleCount"],
        "total_donations": data["totalDonations"],
        "war_day_wins": data["warDayWins"],
        "clan_cards_collected": data["clanCardsCollected"],
        "card_data": data["cards"],
        "favorite_card_id": data["currentFavouriteCard"]["id"],
        "star_points": data["starPoints"],
        "exp_points": data["expPoints"]
    }
    # error handle for members who recently joined the clan, this data will not be populated.
    try:
        player_specific_data.update({"prev_season_trophy_high": data["leagueStatistics"]["previousSeason"]["bestTrophies"]})
        player_specific_data.update({"prev_season_trophies": data["leagueStatistics"]["previousSeason"]["trophies"]})
        player_specific_data.update({"prev_season_id": data["leagueStatistics"]["previousSeason"]["id"]})
    except KeyError:
        player_specific_data.update({"prev_season_trophy_high": "-1"})
        player_specific_data.update({"prev_season_trophies": "-1"})
        player_specific_data.update({"prev_season_id": "-1"})
    try:
        player_specific_data.update({"best_season_id": data["leagueStatistics"]["bestSeason"]["id"]})
        player_specific_data.update({"best_season_trophy_high": data["leagueStatistics"]["bestSeason"]["trophies"]})
    except KeyError:
        player_specific_data.update({"best_season_id": "-1"})
        player_specific_data.update({"best_season_trophy_high": "-1"})
    return player_specific_data


def scrape_battle_data(player_tag_name):
    player_battle_data = []
    endpoint = "/players/%23{}/battlelog".format(player_tag_name[0])
    r = get_request(endpoint)
    response = urllib.request.urlopen(r).read().decode("utf-8")
    data = json.loads(response)
    for battle in data:
        battle_data = {
            "player_tag": player_tag_name[0],
            "player_name": player_tag_name[1],
            "battle_type": battle["type"],
            "battle_time": format_date(battle["battleTime"]),
            "is_ladder_tournament": battle["isLadderTournament"],
            "arena_id": battle["arena"]["id"],
            "arena_name": battle["arena"]["name"],
            "game_mode_id": battle["gameMode"]["id"],
            "game_mode_name": battle["gameMode"]["name"],
            "deck_selection": battle["deckSelection"],
            "team": battle["team"],
            "opponent": battle["opponent"],
            "is_hosted_match": battle["isHostedMatch"]
        }
        player_battle_data.append(battle_data)
    return player_battle_data


def scrape_river_race_data():
    river_race_data = []
    endpoint = "/clans/%23{}/riverracelog".format(clan_tag)
    r = get_request(endpoint)
    response = urllib.request.urlopen(r).read().decode("utf-8")
    data = json.loads(response)
    for week in data["items"]:
        for clan in week["standings"]:
            if (clan["clan"]["tag"])[1:] == clan_tag:
                river_race_week = {
                    "created_date": week["createdDate"],
                    "season_id": week["seasonId"],
                    "section_index": week["sectionIndex"],
                    "completion_rank": clan["rank"],
                    "trophy_change": clan["trophyChange"],
                    "fame": clan["clan"]["fame"],
                    "repair_points": clan["clan"]["repairPoints"],
                    "finish_time": clan["clan"]["finishTime"],
                    "participants": clan["clan"]["participants"],
                    "period_points": clan["clan"]["periodPoints"],
                    "clan_score": clan["clan"]["clanScore"]
                }
                river_race_data.append(river_race_week)
    return river_race_data


def write_player_data(conn, clan_data):
    cur = conn.cursor()
    for player in clan_data:
        sql = ("INSERT INTO clan_table (player_tag, name, role, last_seen, xp_level, trophies, arena_id, arena_name, clan_rank, previous_clan_rank, donations, donation_received, clan_chest_points, trophy_high, total_wins, total_losses, battle_count, three_crown_wins, challenge_cards_won, challenge_max_wins, tourney_cards_won, tourney_battle_count, total_donations, war_day_wins, clan_cards_collected, prev_season_trophies, prev_season_id, prev_season_trophy_high, best_season_id, best_season_trophy_high, card_data, favorite_card_id, star_points, exp_points)"
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            "ON DUPLICATE KEY UPDATE "
                "name = VALUES(name),"
                "role = VALUES(role),"
                "last_seen = VALUES(last_seen),"
                "xp_level = VALUES(xp_level),"
                "trophies = VALUES(trophies),"
                "arena_id = VALUES(arena_id),"
                "arena_name = VALUES(arena_name),"
                "clan_rank = VALUES(clan_rank),"
                "previous_clan_rank = VALUES(previous_clan_rank),"
                "donations = VALUES(donations),"
                "donation_received = VALUES(donation_received),"
                "clan_chest_points = VALUES(clan_chest_points),"
                "trophy_high = VALUES(trophy_high),"
                "total_wins = VALUES(total_wins),"
                "total_losses = VALUES(total_losses),"
                "battle_count = VALUES(battle_count),"
                "three_crown_wins = VALUES(three_crown_wins),"
                "challenge_cards_won = VALUES(challenge_cards_won),"
                "challenge_max_wins = VALUES(challenge_max_wins),"
                "tourney_cards_won = VALUES(tourney_cards_won),"
                "tourney_battle_count = VALUES(tourney_battle_count),"
                "total_donations = VALUES(total_donations),"
                "war_day_wins = VALUES(war_day_wins),"
                "clan_cards_collected = VALUES(clan_cards_collected),"
                "prev_season_trophies = VALUES(prev_season_trophies),"
                "prev_season_id = VALUES(prev_season_id),"
                "prev_season_trophy_high = VALUES(prev_season_trophy_high),"
                "best_season_id = VALUES(best_season_id),"
                "best_season_trophy_high = VALUES(best_season_trophy_high),"
                "card_data = VALUES(card_data),"
                "favorite_card_id = VALUES(favorite_card_id),"
                "star_points = VALUES(star_points),"
                "exp_points = VALUES(exp_points);")
        data = (clan_data[player]["tag"],
                clan_data[player]["name"],
                clan_data[player]["role"],
                format_date(clan_data[player]["lastSeen"]),
                clan_data[player]["xp_level"],
                clan_data[player]["trophies"],
                clan_data[player]["arena_id"],
                clan_data[player]["arena_name"],
                clan_data[player]["clanRank"],
                clan_data[player]["previousClanRank"],
                clan_data[player]["donations"],
                clan_data[player]["donation_received"],
                clan_data[player]["clanChestPoints"],
                clan_data[player]["trophy_high"],
                clan_data[player]["total_wins"],
                clan_data[player]["total_losses"],
                clan_data[player]["battle_count"],
                clan_data[player]["three_crown_wins"],
                clan_data[player]["challenge_cards_won"],
                clan_data[player]["challenge_max_wins"],
                clan_data[player]["tourney_cards_won"],
                clan_data[player]["tourney_battle_count"],
                clan_data[player]["total_donations"],
                clan_data[player]["war_day_wins"],
                clan_data[player]["clan_cards_collected"],
                clan_data[player]["prev_season_trophies"],
                clan_data[player]["prev_season_id"],
                clan_data[player]["prev_season_trophy_high"],
                clan_data[player]["best_season_id"],
                clan_data[player]["best_season_trophy_high"],
                json.dumps(clan_data[player]["card_data"], indent=4),
                clan_data[player]["favorite_card_id"],
                clan_data[player]["star_points"],
                clan_data[player]["exp_points"]
                )
        cur.execute(sql, data)
        conn.commit()
        print("record inserted.")


def write_battle_data(conn, battle_data):
    cur = conn.cursor()
    for battle in battle_data:
        sql = (
            "INSERT INTO clan_battle_history (player_tag, player_name, battle_type, battle_time, is_ladder_tournament, arena_id, arena_name, game_mode_id, game_mode_name, deck_selection, team, opponent, is_hosted_match)"
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            "ON DUPLICATE KEY UPDATE "
                "player_tag = player_tag"
            )
        data = (battle["player_tag"],
                battle["player_name"],
                battle["battle_type"],
                battle["battle_time"],
                battle["is_ladder_tournament"],
                battle["arena_id"],
                battle["arena_name"],
                battle["game_mode_id"],
                battle["game_mode_name"],
                battle["deck_selection"],
                json.dumps(battle["team"], indent=4),
                json.dumps(battle["opponent"], indent=4),
                battle["is_hosted_match"]
                )
        cur.execute(sql, data)
        conn.commit()
        print("battle inserted.")


def write_river_race_data(conn, river_race_data):
    cur = conn.cursor()
    for week in river_race_data:
        sql = (
            "INSERT INTO river_race_history (created_date, season_id, section_index, completion_rank, trophy_change, fame, repair_points, finish_time, participants, period_points, clan_score)"
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            "ON DUPLICATE KEY UPDATE "
            "created_date = created_date"
        )
        data = (format_date(week["created_date"]),
                week["season_id"],
                week["section_index"],
                week["completion_rank"],
                week["trophy_change"],
                week["fame"],
                week["repair_points"],
                format_date(week["finish_time"]),
                json.dumps(week["participants"], indent=4),
                week["period_points"],
                week["clan_score"]
                )
        cur.execute(sql, data)
        conn.commit()
        print("river-race week inserted.")
    return


def scrape_player_clan_data():
    player_clan_data = {}
    endpoint = "/clans/%23{}/members".format(clan_tag)
    r = get_request(endpoint)
    response = urllib.request.urlopen(r).read().decode("utf-8")
    data = json.loads(response)
    for item in data["items"]:
        # add only the desired information to a new dict for each player
        player_data = {item["tag"][1:]: {
            "tag": item["tag"][1:],
            "lastSeen": item["lastSeen"],
            "clanRank": item["clanRank"],
            "previousClanRank": item["previousClanRank"],
            "clanChestPoints": item["clanChestPoints"]
            }
        }
        player_clan_data.update(player_data)
    return player_clan_data


def format_date(unformatted_date):
    # example: "20220328T050759.000Z" "yyyymmddThhmmss.sssZ"
    # goal: yyyy-mm-dd hh:mm:ss unformatted_date
    formatted_date = datetime.strptime(unformatted_date[:-5], "%Y%m%dT%H%M%S")
    return formatted_date


def get_player_tag_names(clan_data):
    player_tag_names = []
    for player in clan_data:
        player_tag_names.append((clan_data[player]["tag"],clan_data[player]["name"]))
    return player_tag_names


def webscrape():
    today = date.today()
    weekdayindex = today.weekday()
    weekday = weekDays[weekdayindex] # for readability
    clan_data = scrape_clan_data()
    player_tag_list = get_player_tag_names(clan_data)
    conn = mysqlconnect()
    write_player_data(conn, clan_data)
    for player_tag_name in player_tag_list:
        battle_data = scrape_battle_data(player_tag_name) #scrapes the last ~ 35 battles for each clan member
        write_battle_data(conn, battle_data) #writes the last ~35 battles for each player into the DB
    if weekday == "Monday":
        river_race_data = scrape_river_race_data()
        write_river_race_data(conn, river_race_data)
    conn.close()

#  Driver Code
if __name__ == "__main__":
    # ************* PRODUCTION CODE *********** #
    #run every day at 1pm
    schedule.every().day.at("17:00").do(webscrape)
    while True:
        schedule.run_pending()
        time.sleep(1)
    # ************* DEVELOPMENT CODE *********** #
    # webscrape()



