import pandas as pd
import datetime
from dateutil.relativedelta import relativedelta
import numpy as np
from chessratings import uscf_elo
from itertools import combinations
pd.set_option('mode.chained_assignment', None)


def nearest(items, pivot):
    return min(items, key=lambda x: abs(x - pivot))


def compute_date(scrape_date, review_date, review_time_ago):
    review_month = review_date[5:8]
    review_day = review_date[-20:-18].strip()

    if 'over' in review_time_ago:
        crop_offset_string = review_time_ago.split('over')[1].strip()
        offset_period = int(crop_offset_string[:2].strip())

        min_date = scrape_date - relativedelta(months=12*(offset_period+1))
        max_date = scrape_date - relativedelta(months=12*offset_period)

        candidate_years = [min_date.year, max_date.year]
        candidate_dates = [datetime.datetime.strptime(
            review_day + ' ' + review_month + ' ' + str(y), '%d %b %Y') for y in candidate_years]

        final_review_date = [
            d for d in candidate_dates if d > min_date and d < max_date][0]

    elif 'almost' in review_time_ago:
        crop_offset_string = review_time_ago.split('almost')[1].strip()
        offset_period = int(crop_offset_string[:2].strip())

        min_date = scrape_date - relativedelta(months=12*offset_period)
        max_date = scrape_date

        candidate_years = [min_date.year, max_date.year]
        candidate_dates = [datetime.datetime.strptime(
            review_day + ' ' + review_month + ' ' + str(y), '%d %b %Y') for y in candidate_years]

        final_review_date = [
            d for d in candidate_dates if d > min_date and d < max_date][0]

    else:
        if 'about' in review_time_ago:
            crop_offset_string = review_time_ago.split('about')[1].strip()
            offset_period = int(crop_offset_string[:2].strip())
        else:
            offset_period = int(review_time_ago[:2].strip())

        if 'month' in review_time_ago:
            offset_scrape_date = scrape_date - \
                relativedelta(months=offset_period)
        elif 'year' in review_time_ago:
            offset_scrape_date = scrape_date - \
                relativedelta(months=12*offset_period)
        else:
            offset_scrape_date = scrape_date

        candidate_years = [offset_scrape_date.year - 1,
                           offset_scrape_date.year, offset_scrape_date.year + 1]
        try:
            candidate_dates = [datetime.datetime.strptime(
                review_day + ' ' + review_month + ' ' + str(y), '%d %b %Y') for y in candidate_years]
        # in some fringe cases, we may be dealing with February 29th, which only exists on leap years
        except ValueError:
            candidate_dates = [datetime.datetime.strptime(str(int(
                review_day) - 1) + ' ' + review_month + ' ' + str(y), '%d %b %Y') for y in candidate_years]

        final_review_date = nearest(candidate_dates, offset_scrape_date)

    return final_review_date


def clean_wine_reviews(review_df):

    review_df['final_review_date'] = review_df.apply(lambda x: compute_date(
        x['scrape_date'], x['review_date'], x['review_time_ago']), axis=1)

    # drop any reviews that don't have a vintage specified. N.V. is acceptable, but blank vintage is not.
    review_df['vintage'].replace({'': np.nan}, inplace=True)
    review_df.dropna(subset=['vintage'], axis=0, inplace=True)

    just_reviews = review_df[['wine_id', 'reviewer',
                              'vintage', 'rating', 'final_review_date']]
    return just_reviews


def compute_head_to_head_result(wine_0, wine_1, rating_0, rating_1):
    if rating_0 > rating_1:
        return wine_0
    elif rating_0 < rating_1:
        return wine_1
    else:
        return np.nan


def player_info_lookup(wine_id, score_lookup_table):
    score_lookup_table_filtered = score_lookup_table.loc[
        score_lookup_table['wine_id'] == wine_id]
    if score_lookup_table_filtered.empty:
        elo_rating = None
        tournament_number = 0
        nr_games_played = 0
        nr_wins = 0
        nr_losses = 0
    else:
        score_lookup = score_lookup_table_filtered.loc[score_lookup_table_filtered['tournament_number'] == max(
            score_lookup_table_filtered['tournament_number'])].iloc[0]
        elo_rating = score_lookup['elo_rating']
        tournament_number = score_lookup['tournament_number']
        nr_games_played = sum(score_lookup_table_filtered['nr_games_played'])
        nr_wins = sum(score_lookup_table_filtered['nr_wins'])
        nr_losses = sum(score_lookup_table_filtered['nr_losses'])

    return elo_rating, tournament_number, nr_games_played, nr_wins, nr_losses


def match_format(combo, review_table):
    id_0 = combo[0]
    id_1 = combo[1]
    rating_0 = review_table.at[combo[0], 'rating']
    rating_1 = review_table.at[combo[1], 'rating']

    # note: still need to fix this
    if isinstance(rating_0, float) and isinstance(rating_1, float):
        result = compute_head_to_head_result(id_0, id_1, rating_0, rating_1)
        match_result = ((id_0, id_1), result)

        return match_result


def run_tournaments(review_df, score_lookup_table):
    review_dates = sorted(list(set(review_df['final_review_date'])))
    for r in review_dates:
        review_df_date = review_df.loc[review_df['final_review_date'] == r]
        reviewers = sorted(list(set(review_df_date['reviewer'])))
        for u in reviewers:
            review_df_slice = review_df_date.loc[review_df_date['reviewer'] == u]
            # In some rare cases, an individual may have rated an individual wine more than once in one day. In this case, we eliminate one of these reviews
            review_df_slice = review_df_slice[~review_df_slice.index.duplicated(
                keep='first')]

            players = []
            unique_players = list(set(review_df_slice.index))

            for u in unique_players:
                rating, tournament_number, nr_games_played, nr_wins, nr_losses = player_info_lookup(
                    u, score_lookup_table)
                p = uscf_elo.Player(u, rating, nr_games_played,
                                    nr_wins, nr_losses, tournament_number)
                players.append(p)

            combos = list(combinations(review_df_slice.index, 2))
            tournament_results = []
            for c in combos:
                match_result = match_format(c, review_df_slice)
                tournament_results.append(match_result)

            tournament = uscf_elo.Tournament(
                players=players, tournament_results=tournament_results, tournament_date=r)
            if tournament.valid_tournament:
                try:
                    updated_scores = tournament.run_tournament()
                    updated_scores_with_reviewer = [
                        v.append(u) for u in updated_scores]
                    score_lookup_entry_table = pd.DataFrame(updated_scores_with_reviewer, columns=[
                                                            'wine_id', 'tournament_date', 'tournament_number', 'nr_games_played', 'nr_wins', 'nr_draws', 'nr_losses', 'elo_rating', 'reviewer'])
                    score_lookup_table = score_lookup_table.append(
                        score_lookup_entry_table)
                except:
                    continue

    return score_lookup_table
    # [print(u) for u in updated_scores]
