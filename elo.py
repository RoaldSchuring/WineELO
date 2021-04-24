import numpy as np
from datetime import date


class Player:

    epsilon_special_rating = 10**-7

    def compute_age_based_rating(self, birth_date=date.fromisoformat('1990-01-01'), tournament_end_date=date.fromisoformat('2021-01-01')):
        age = (tournament_end_date - birth_date)/365.25
        if age < 2:
            rating = 100
        elif 2 <= age <= 26:
            rating = 50*age
        else:
            rating = 1300
        return rating

    def initialize_rating(self):
        if self.pre_tournament_rating is None:
            initial_rating = self.compute_age_based_rating()
        else:
            initial_rating = self.pre_tournament_rating
        return initial_rating

    def __init__(self, pre_tournament_rating, nr_games_played, nr_wins, nr_losses):
        self.nr_games_played = nr_games_played
        self.nr_wins = nr_wins
        self.nr_losses = nr_losses
        self.pre_tournament_rating = pre_tournament_rating
        self.initial_rating = self.initialize_rating()

    def compute_effective_nr_games(self):
        if self.initial_rating <= 2355:
            n = 50/np.sqrt(0.662 + 0.00000739*(2569 -
                           self.initial_rating)**2)
        else:
            n = 50

        effective_nr_games = min(n, self.nr_games_played)
        return effective_nr_games

    def compute_rating_type(self):
        if self.nr_games_played <= 8:
            rating_type = 'special-new'
        elif self.nr_wins == self.nr_games_played:
            rating_type == 'special-only-wins'
        elif self.nr_losses == self.nr_games_played:
            rating_type = 'special-only-losses'
        else:
            rating_type = 'standard'
        return rating_type

    def compute_pwe(self, player_rating, opponent_rating):
        if player_rating <= opponent_rating - 400:
            pwe = 0
        elif opponent_rating - 400 < player_rating < opponent_rating + 400:
            pwe = 0.5 + (player_rating - opponent_rating)/800
        else:
            pwe = 1

        return pwe

    # players with <= 8 games, or players that have had only wins/losses in all previous rated games, get a special rating

    def compute_adjusted_initial_rating_and_score(self, tournament_results, effective_nr_games, rating_type):

        # tournament results must be structured as a list of tuples (rating, opponent_rating, result)
        tournament_score = sum([i[2] for i in tournament_results])

        if rating_type == 'special-only-wins':
            adjusted_initial_rating = self.initial_rating - 400
            adjusted_score = tournament_score + effective_nr_games
        elif rating_type == 'special-only-losses':
            adjusted_initial_rating = self.initial_rating + 400
            adjusted_score = tournament_score
        else:
            adjusted_initial_rating = self.initial_rating
            adjusted_score = tournament_score + effective_nr_games/2

        return adjusted_initial_rating, adjusted_score

    def special_rating_objective(tournament_results, effective_nr_games, adjusted_initial_rating, adjusted_score, special_rating_estimate)
    # tournament results must be structured as a list of tuples (rating, opponent_rating, result)
    sum_pwe = sum([self.compute_pwe(M, t[1]) for t in tournament_results])
    rating_type = self.compute_rating_type()

    objective_fn = effective_nr_games * \
        self.compute_pwe(special_rating_estimate, adjusted_initial_rating) + \
        sum_pwe - adjusted_score

    return objective_fn

    def compute_special_rating(self, rating, effective_nr_games, tournament_results):

        tournament_games = len(tournament_results)
        tournament_score = sum([t[2] for t in tournament_results])
        opponent_ratings = [r[1] for r in tournament_results]
        adjusted_initial_rating, adjusted_score = self.compute_adjusted_initial_rating_and_score(
            tournament_results, effective_nr_games, rating_type)

        M = (effective_nr_games*self.initial_rating + sum(opponent_ratings) + 400 *
             (2*tournament_score - tournament_games))/(effective_nr_games + tournament_games)

        f_M = self.special_rating_objective(
            tournament_results, effective_nr_games, adjusted_initial_rating, adjusted_score, M)

        Sz = [o + 400 for o in opponent_ratings] + \
            [o - 400 for r in opponent_ratings]

        if f_M > epsilon_special_rating:
            step_2_satisfied = False
            while step_2_satisfied is False:

                # Let za be the largest value in Sz for which M > za.
                za = max([z for z in Sz if z < M])

                f_za = self.special_rating_objective(
                    tournament_results, effective_nr_games, adjusted_initial_rating, adjusted_score, za)

                if abs(f_M - f_za) < epsilon_special_rating:
                    M = za
                    f_M = f_za
                    continue
                else:
                    M_star = M - f_M * ((M - za) / (f_M - f_za))
                    if M_star < za:
                        M = za
                        f_M = f_za
                        continue
                    elif za <= M_star < M:
                        M = M_star
                        f_M = self.special_rating_objective(
                            tournament_results, effective_nr_games, adjusted_initial_rating, adjusted_score, M_star)
                        continue
                    else:
                        step_2_satisfied = True
                        break

        if f_M < -epsilon_special_rating:
            step_3_satisfied = False
            while step_3_satisfied is False:

                zb = min([z for z in Sz if z > M])
                f_zb = self.special_rating_objective(
                    tournament_results, effective_nr_games, adjusted_initial_rating, adjusted_score, zb)

                if abs(f_zb - f_M) < epsilon_special_rating:
                    M = zb
                    f_M = f_zb
                else:
                    M_star = M - f_M * ((zb - M) / (f_zb - f_M))
                    if M_star > zb:
                        M = zb
                        continue
                    elif M < M_star <= zb:
                        M = M_star
                        f_M = self.special_rating_objective(
                            tournament_results, effective_nr_games, adjusted_initial_rating, adjusted_score, M_star)
                        continue
                    else:
                        step_3_satisfied = True
                        break

        if abs(f_M) < -epsilon_special_rating:
            p = len([o for o in opponent_ratings if abs(M - o) <= 400])
            if abs(M - adjusted_initial_rating) <= 400:
                p += 1
            if p > 0:
                pass
            elif p == 0:
                za = max([s for s in Sz if s < M])
                zb = min([s for s in Sz if s > M])
                if za <= self.initial_rating <= zb:
                    M = self.initial_rating
                elif self.initial_rating < za:
                    M = za
                elif self.initial_rating > zb:
                    M = zb
                else:
                    raise Exception(
                        'M is outside the range of expected values.')

            M = min(2700, M)
            return M
