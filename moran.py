# Python 3

from __future__ import print_function

import csv
from collections import defaultdict, Counter
import itertools
from pathlib import Path
import random
import sys

import numpy as np

import axelrod as axl


def output_players(players, outfilename="players.csv"):
    """Cache players to disk for later retrieval."""
    rows = [(i, str(player), player.classifier["stochastic"]) for (i, player) in enumerate(players)]
    path = Path("results") / outfilename
    with path.open('w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(rows)

def build_population(players, weights):
    population = []
    for player, weight in zip(players, weights):
        for _ in range(weight):
            population.append(player.clone())
    return population

def run_simulations(players, N=2, turns=100, repetitions=1000, noise=0, outfilename=None):
    """This function conducts many moran processes to empirically estimate
    fixation probabilities. For each pair of strategies, the population consists
    of 1 player of the first type and N-1 players of the second type."""
    path = Path("results")
    if not outfilename:
        outfilename = "sims_{N}.csv".format(N=N)
    path = path / outfilename
    outfile = csv.writer(path.open('a'))

    # Cache names to reverse winners to ids later
    names_inv = dict(zip([str(p) for p in players], range(len(players))))

    # For each distinct pair of players, play `repetitions` number of Moran matches
    for i, player_1 in enumerate(players):
        print(i, len(players))
        for j, player_2 in enumerate(players):
            if i == j:
                continue
            if player_1.classifier["stochastic"] and player_2.classifier["stochastic"]:
                continue
            rows = []
            initial_population = build_population([player_1, player_2], [1, N-1])
            mp = axl.MoranProcess(initial_population, turns=turns, noise=noise)
            for _ in range(repetitions):
                mp.reset()
                populations = mp.play()
                winner_name = mp.winning_strategy_name
                row = [i, j, names_inv[winner_name]]
                rows.append(row)
            outfile.writerows(rows)

def relative_fitnesses_deterministic(strategies, turns=100):
    """For deterministic strategies we can compute the fixation probability
    from the relative fitness. Input strategies are assumed deterministic."""
    fitness = []
    for i, player1 in strategies:
        for j, player2 in strategies:
            match = axl.Match((player1, player2), turns=turns)
            match.play()
            match_scores = np.sum(match.scores(), axis=0) / float(turns)
            fitness.append((i, j, match_scores[0], match_scores[1]))
    path = Path("results") / "deterministic.csv"
    with path.open('w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(fitness)

def filter_strategies(strategies):
    stochastic = []
    deterministic = []
    for i, strategy in enumerate(strategies):
        if strategy.classifier["stochastic"]:
            stochastic.append((i, strategy))
        else:
            deterministic.append((i, strategy))
    return stochastic, deterministic

def do_deterministic(strategies, turns):
    stochastic, deterministic = filter_strategies(strategies)
    relative_fitnesses_deterministic(deterministic, turns=turns)

def main():
    N = int(sys.argv[1]) # Population size
    try:
        repetitions = int(sys.argv[2])
    except IndexError:
        repetitions = 1000
    turns = 100
    # Make sure the data folder exists
    path = Path("results")
    path.mkdir(exist_ok=True)

    strategies = list(map(lambda x: x(), axl.ordinary_strategies))
    output_players(strategies)
    #do_deterministic(strategies, turns=turns)

    run_simulations(strategies, N=N, repetitions=repetitions, turns=turns)

if __name__ == "__main__":
    main()
