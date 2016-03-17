'''
This script is written by Mike Ngan in 2016 to predict the NCAA tournament not by skill 
but by capturing the teams that are the most undervalued according to 538's predictions
removing pick biases by Yahoo users. Many functions are not made to be elegant but 
speed efficient on the each-run level.  Paralleled to optimally run on multicore (16+) 
machines.

2016 Conclusion: Virginia is extremely under priced.
'''

import csv
from itertools import izip
import random
import time
import multiprocessing

def get_winner(team1,team2,round,style):
    team1_stats = team1[team1.keys()[0]]
    team2_stats = team2[team2.keys()[0]]
    if style == 'rand': #this adds jitter to add to randomness for "my bracket"
        if (team1_stats['pick_prob'][round]) / ((team1_stats['pick_prob'][round]) + (team2_stats['pick_prob'][round] * random.uniform(.5, 1.5))) > random.uniform(0, 1): #team 1 wins
            return team1
        else:
            return team2
    else:
        if (team1_stats[style][round]) / ((team1_stats[style][round]) + (team2_stats[style][round])) > random.uniform(0, 1): #team 1 wins
            return team1
        else:
            return team2
        
def do_round(teams, style):
    find_round = len(teams)
    rd = None
    if find_round == 64:
        rd = 0
    elif find_round == 32:
        rd = 1
    elif find_round == 16:
        rd = 2
    elif find_round == 8:
        rd = 3
    elif find_round == 4:
        rd = 4
    elif find_round == 2:
        rd = 5
    winners = []
    for x, y in pairwise(teams): #get winner for every matchup
        winners.append(get_winner(x,y,rd,style))
    return winners

def make_bracket(stats, style): #make a bracket based on style (pick like a user or based on 538 stats)
    win_32 = do_round(stats,style)    
    win_16 = do_round(win_32,style)
    win_8 = do_round(win_16,style)
    win_4 = do_round(win_8,style)
    win_2 = do_round(win_4,style)
    win_1 = do_round(win_2,style)
    return [win_32,win_16,win_8,win_4,win_2,win_1]
    
def write_bracket(a, win_percent): #save the output
    with open(str(win_percent) + ".csv", "wb") as f:
        writer = csv.writer(f)
        writer.writerows(a)
    return 0

def score(actual,bracket):
    score_scheme = {0:1,1:2,2:4,3:8,4:16,5:32}
    the_score = 0

    for i, val in enumerate(bracket):
        rd_correct = 0
        for j, val2 in enumerate(val):
            for k in actual[i]:
                if bracket[i][j].keys()[0] == k.keys()[0]:
                    rd_correct += 1
        the_score += rd_correct * score_scheme[i]
    return the_score

def trial(my_bracket, competition, stats):
    winning_bracket = make_bracket(stats,'win_prob')
    my_score = score(my_bracket,winning_bracket)
    win = 1
    for bracket in competition:
        if score(bracket,winning_bracket) > my_score:
            win = 0
            break
    return win

def pairwise(iterable):
    "s -> (s0, s1), (s2, s3), (s4, s5), ..."
    a = iter(iterable)
    return izip(a, a)

def main():
    reader = csv.reader(open('NCAATourneyStats_noheader.csv', 'r'))
    stats = []
    for row in reader:
        stats.append({row[0]:{'win_prob':row[1:7],'pick_prob':row[7:]}}) 
    
    for i in stats:
        i[i.keys()[0]]['win_prob'] = map(float, i[i.keys()[0]]['win_prob'])
        i[i.keys()[0]]['pick_prob'] = map(float, i[i.keys()[0]]['pick_prob'])
    
    highest_odds = 0
    tests = 2500
    num_competitors = 300
    
    the_competition = []
    for i in xrange(num_competitors):
        this_bracket = make_bracket(stats,'pick_prob')
        the_competition.append(this_bracket)
    
    #Run samples
    while True:
        my_bracket = make_bracket(stats,'rand')
        wins = []
        
        pool = multiprocessing.Pool()
        for i in range(tests):
            wins.append(pool.apply_async(trial, args=(my_bracket,the_competition,stats)))
        pool.close()
        pool.join()

        win_total = 0        
        for r in wins:
            win_total += r.get()
        
        win_percentage = (win_total*1.0) / tests
        
        if highest_odds < win_percentage:
            highest_odds = win_percentage
            write_bracket(my_bracket,win_percentage)
        
        #break #break loop for testing time

if __name__ == "__main__":
    start_time = time.time()
    main()    
    print("%s seconds" % (time.time() - start_time)) #stop watch
