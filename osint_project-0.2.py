import time
from selenium.webdriver.common.by import By
from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd

# -----------------------------------------------------------------
# Config
# -----------------------------------------------------------------
region = "EU"
#base_url1 = "https://ironforge.pro/pvp/leaderboards/EU/2/"
base_url1 = "https://ironforge.pro/pvp/leaderboards/" + region +  "/2/"
base_url2 = "https://ironforge.pro/pvp/player/"
chart = pd.DataFrame(columns=['Rank', 'Rating', 'Name', 'Class', 'Server', 'W/L', 'Wins%'])
teams_2v2 = pd.DataFrame(columns=['Player 1', 'Player 2', 'Team Composition', 'Server', 'Match%'])
team_search_interval = 10
nb_match_check = 10
browser_sleep = 5
teamOutputFile = "teams_2v2_" + region + ".csv"
chartOutputFile = "chart_2v2_"+ region + ".csv"
# -----------------------------------------------------------------
# Functions
# -----------------------------------------------------------------
def load_url(url):
    browser.get(url)
    # wait until DOM will load complete
    time.sleep(browser_sleep) 

def populate_charts():
    load_url(base_url1)
    trs = browser.find_elements(By.XPATH,"//table[@class='leaderboards__table']/tbody/tr")
    # loop to populate chart df data
    # skip trs[0]
    for i in range(1, len(trs)):
        tds = trs[i].find_elements(By.TAG_NAME, "td")
        stats = []
        # skip tds[0]
        for j in range(1,len(tds)):
            stats.append(tds[j].text)
        # skip when no stats
        if stats != []:
            chart.loc[len(chart)] = stats

def compare_match_dates(refList, url):
    load_url(url)
    tds = browser.find_elements(By.XPATH,"//td[@class='a__table_date a__table_date_short']")
    dates = []
    if len(tds) < nb_match_check:
        return -1
    for i in range(0, nb_match_check):
        dates.append(tds[i].text)
    result = [x for x in refList if x in dates]
    return len(result)*100/nb_match_check

def dump_values(pseudo, server, url):
    print("pseudo = [" + pseudo + "] -  server = [" + server + "] - url = [" + url + "]")

def search_teammate():
    for i in range(0, chart.shape[0]):
    #for i in range(0, 5):
        percent_confidence = 0
        mate_index=i
        potential_mate_class = ""
        potential_mate_pseudo = ""
        potential_mate_server = ""
        player_pseudo = ""
        player_server = ""
        player_class = ""
        mate_pseudo = ""
        mate_class = ""
        player_class = chart.iloc[i][3]
        if (player_class == ""):
            # skip when no class
            i+=1
            continue
        player_pseudo = chart.iloc[i][2]
        player_server = chart.iloc[i][4]
        player_match_url = base_url2 + player_server + "/" + player_pseudo + "/"
        #dump_values (player_pseudo, player_server, player_match_url)
        load_url(player_match_url)
        tds = browser.find_elements(By.XPATH,"//td[@class='a__table_date a__table_date_short']")
        if len(tds) < nb_match_check:
            continue
        player_dates = []
        for j in range(0, nb_match_check):
            player_dates.append(tds[j].text)
        before_search_interval = 5
        after_search_interval = 5
        if i < team_search_interval:
            before_search_interval =  i
        if (chart.shape[0] -i) < team_search_interval:
            after_search_interval = chart.shape[0] - i
        # search mate backward
        for j in range (1, before_search_interval+1):
            potential_mate_class = chart.iloc[i-j][3]
            if (potential_mate_class == ""):
                j+=1
                continue
            potential_mate_pseudo = chart.iloc[i-j][2]
            potential_mate_server = chart.iloc[i-j][4]            
            # if potential mate is not on the same server as player then skip
            if potential_mate_server != player_server:
                j+=1
                continue
            potential_mate_url = base_url2 + potential_mate_server + "/" + potential_mate_pseudo + "/"
            #dump_values (potential_mate_pseudo, potential_mate_server, potential_mate_url)
            tmp_percent_confidence = compare_match_dates(player_dates, potential_mate_url)
            #print (str(tmp_percent_confidence) + "%")
            if tmp_percent_confidence > percent_confidence:
                percent_confidence = tmp_percent_confidence
                mate_class = potential_mate_class
                mate_pseudo = potential_mate_pseudo
                mate_index = i-j
        # search mate forward
        for j in range (1, after_search_interval+1):
            if (i+j) >= 100:
                j+=1
                continue
            potential_mate_class = chart.iloc[i+j][3]
            if (potential_mate_class == ""):
                j+=1
                continue
            potential_mate_pseudo = chart.iloc[i+j][2]
            potential_mate_server = chart.iloc[i+j][4]
            # if potential mate is not on the same server as player then skip
            if potential_mate_server != player_server:
                j+=1
                continue
            potential_mate_url = base_url2 + potential_mate_server + "/" + potential_mate_pseudo + "/"
            #dump_values (potential_mate_pseudo, potential_mate_server, potential_mate_url)
            tmp_percent_confidence = compare_match_dates(player_dates, potential_mate_url)
            #print (str(tmp_percent_confidence) + "%")
            if tmp_percent_confidence > percent_confidence:
                percent_confidence = tmp_percent_confidence
                mate_class = potential_mate_class
                mate_pseudo = potential_mate_pseudo
                mate_index = i+j
        print ("player = [" + player_pseudo + "] - mate index = [" + str(mate_index) + "] - mate pseudo  = [" + mate_pseudo + "] - mate confidence = [" + str(percent_confidence) + "%]")
        teams_2v2.loc[len(teams_2v2)] = [player_pseudo, mate_pseudo, player_class + " - " + mate_class, player_server, str(percent_confidence)]
# -----------------------------------------------------------------
# Main
# -----------------------------------------------------------------
# Open web browser
browser=webdriver.Firefox()
populate_charts()
chart.to_csv(chartOutputFile)
search_teammate()
teams_2v2.to_csv(teamOutputFile)

# Close web browser
browser.close()

